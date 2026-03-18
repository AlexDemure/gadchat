# Current System Design

## Components
- Gateway:
  - websocket gateway
  - websocket command intake
  - Kafka command publish
  - Kafka event consume
  - realtime delivery / fanout
  - protocol HTTP docs for websocket topics
- Core:
  - read REST API for snapshots and resync
  - client and internal query endpoints
- Chat Processor:
  - write-side command processor
  - domain validation
  - write DB persistence
  - domain event publish
- Uploader:
  - file ingestion API
- Postgres:
  - write and read persistence
- Kafka:
  - durable transport for commands and domain events
- Redis:
  - regional presence and fanout coordination
- MinIO:
  - binary file storage

## Target Write Path
1. Client sends command through `gateway` websocket.
2. Gateway validates auth and command protocol shape.
3. Gateway publishes command to Kafka.
4. Client receives immediate transport ack.
5. Chat processor consumes command, performs write-side logic, persists DB changes, publishes domain event.
6. Gateway consumes domain event from Kafka and delivers it to local websocket connections.

## Target Read Path
- `core` owns REST snapshot / query endpoints.
- `POST /chats:search` returns chat page with cursor pagination.
- `POST /chats/{chat_id}/messages:search` returns message page with cursor pagination.
- Snapshot and recovery stay on REST.
- Realtime state changes are delivered through websocket deltas from `gateway`.

## Transport Split
- Kafka is the global durable backbone for chat commands and chat events.
- Redis is regional and auxiliary:
  - presence
  - room membership
  - local node coordination
  - ephemeral signals like typing
- Durable chat mutations must not rely on Redis Pub/Sub as the primary transport.

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
- `gateway` is command / realtime transport and Kafka edge.
- `core` is read/query transport.
- REST and WebSocket remain separated by responsibility:
  - REST for snapshot / search / resync
  - WebSocket for commands, acks, statuses, realtime deltas
- Gateway usecases orchestrate publish / consume flow, not write-side business logic.
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

## Current First Migration Step
- Start with `chat.create`.
- Gateway publishes `chat.create.command` to Kafka.
- Gateway consumes `chat.create.event` from Kafka.
- Client receives immediate transport ack and later realtime `chat.create.event`.
