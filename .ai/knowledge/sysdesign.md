# Current System Design

## Components
- Gateway:
  - websocket gateway
  - websocket command intake
  - realtime delivery / fanout
  - protocol HTTP docs for websocket topics
- Core:
  - read REST API for snapshots and resync
  - client and internal query endpoints
- Uploader:
  - file ingestion API
- Postgres:
  - source of truth
- MinIO:
  - binary file storage

## Current Write Path
1. Client sends command through `gateway` websocket.
2. Gateway validates command payload through protocol schema.
3. Gateway write usecase calls `publish(...)` and stores `Event` in DB.
4. Client receives immediate task-style ack with `Event`.
5. Further dispatcher / async processing path is separate from gateway intake.

## Current Read Path
- `core` owns REST snapshot / query endpoints.
- `POST /chats:search` returns chat page with cursor pagination.
- `POST /chats/{chat_id}/messages:search` returns message page with cursor pagination.
- Snapshot and recovery stay on REST.
- Realtime state changes are delivered through websocket deltas from `gateway`.

## Current State Model
- Chat pinning is user-scoped and stored in `Member.position`.
- Unread count is stored in `Member.notifications`.
- Message pinned state is stored in `Message.pinned`.
- Read receipts are stored in `Read`.
- Reply and forward are stored separately in `Reply` and `Forward`.
- Message read model in API is personalized: each user receives only their own `read` object for a message.
- Message attachments / reply / forward are returned as direct read models, not as link-table payloads.

## Architecture Constraints
- `gateway` and `core` are separate services with different responsibilities.
- `gateway` is command / realtime transport.
- `core` is read/query transport.
- REST and WebSocket remain separated by responsibility:
  - REST for snapshot / search / resync
  - WebSocket for commands, acks, statuses, realtime deltas
- Usecases orchestrate business flow.
- CRUD performs query-heavy work like `search(...)`.
- CRUD search methods operate on plain dict payloads from upper layers and should keep query assembly explicit and step-by-step.
- Schemas own request/response serialization.
- HTTP usecase dependencies must close session before response is returned.
- Gateway protocol HTTP docs use topic-style paths:
  - `/chat.create.command`
  - `/chat.position.command`
  - `/message.create.command`
  - `/message.pinned.command`
  - `/message.read.command`
  - `/message.unpinned.command`
