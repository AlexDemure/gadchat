# Current System Design

## Components
- HTTP API:
  - auth
  - chats search/create/position
  - messages create/search/read/pinned
  - files upload/get
- WebSocket layer:
  - only realtime delivery
- Postgres:
  - source of truth
- MinIO:
  - binary file storage

## Current Write Path
1. Client uploads files through `files:upload:*`.
2. Client sends `messages:create` with:
   - optional `text`
   - optional `reply`
   - optional `forward`
   - optional `files` as file ids
3. HTTP layer вызывает usecase напрямую через UoW dependency.
4. Usecase сохраняет:
   - chat if needed for direct chat flow
   - message
   - attachment links
   - reply/forward links
5. WebSocket layer использует БД как source of truth для чтения истории.

## Current Read Path
- `POST /chats:search` returns chat page with cursor pagination.
- `POST /chats/{chat_id}/messages:search` returns message page with cursor pagination.
- `GET /chats/{chat_id}/files/{file_id}` returns file metadata.
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
- HTTP usecase dependencies must close session before response is returned.
