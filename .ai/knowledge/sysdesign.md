# Current System Design

## Components
- HTTP API:
  - auth
  - chats search/create/position
  - messages create/search/read/pinned
  - files upload/get
- WebSocket layer:
  - only realtime delivery
- Kafka:
  - ingress for async message creation
- Worker:
  - consumes ingress events
  - creates message in DB
  - publishes delivery event
- Redis Pub/Sub:
  - inter-pod fanout
- Postgres:
  - source of truth
- MinIO:
  - binary file storage

## Current Write Path
1. Client uploads files through `files:upload:*`.
2. Client sends `messages:create` with:
   - optional `body`
   - optional `reply`
   - optional `forward`
   - optional `attachments` as file ids
3. HTTP layer validates access and publishes ingress event to Kafka.
4. Worker consumes event and persists:
   - chat if needed for direct chat flow
   - message
   - attachment links
   - reply/forward links
5. Worker publishes realtime event to Redis.
6. WebSocket manager fans out to local connections.

## Current Read Path
- `POST /chats:search` returns chat page with cursor pagination.
- `POST /chats/{chat_id}/messages:search` returns message page with cursor pagination.
- `GET /chats/{chat_id}/files/{file_id}` returns binary file content.
- `PUT /chats/{chat_id}/messages/{message_id}:read` marks messages as read.

## Current State Model
- Chat pinning is user-scoped and stored in `Member.position`.
- Unread count is stored in `Member.notifications`.
- Message pinned state is stored in `Message.pinned`.
- Read receipts are stored in `Read`.
- Reply and forward are stored separately in `Reply` and `Forward`.

## Architecture Constraints
- REST and WebSocket remain separated.
- Usecases orchestrate business flow.
- CRUD performs query-heavy work like `search(...)`.
- Schemas own request/response serialization.
