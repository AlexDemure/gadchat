# TODO: Chat MVP -> Production Ready

## 1) Security and auth boundary
- [ ] Move WS ticket secret from code to env (`CHAT_SERVICE_SECRET`), support key rotation.
- [ ] Add ticket TTL config in env and enforce max TTL.
- [ ] Add basic rate limit for `POST /ws-ticket` and `POST /messages`.

## 2) Message reliability
- [ ] Add idempotency key for message send (`X-Idempotency-Key` or body field).
- [ ] Add DB unique constraint for idempotent message creation.
- [ ] Add retry/DLQ policy for Kafka consumer failures.
- [ ] Add outbox pattern (or equivalent) for safer DB + event publish consistency.

## 3) Database and performance
- [ ] Rework `GET /chats` query to remove N+1 reads.
- [ ] Add composite indexes for hot paths:
  - [ ] `message(chat_id, created DESC, id DESC)`
  - [ ] `member(user_id, chat_id)`
  - [ ] `message_file(message_id, position)`
- [ ] Validate partition count and add migration strategy for partition expansion.
- [ ] Add retention/archival policy for old messages and media metadata.

## 4) WebSocket scalability
- [ ] Replace sequential push with per-connection buffered send queues.
- [ ] Add backpressure policy (drop/close/slow-consumer handling).
- [ ] Add connection limits per user and per pod.
- [ ] Add heartbeat timeouts and stale socket cleanup metrics.

## 5) Observability and operations
- [ ] Add structured logs with request/event correlation IDs.
- [ ] Add metrics (Prometheus): p95/p99 API, WS active conns, fanout latency, Kafka lag.
- [ ] Add readiness/liveness checks for DB, Redis, Kafka, MinIO dependencies.
- [ ] Add dashboards and alerting thresholds.

## 6) Tests and load validation
- [ ] Add unit tests for usecases (`messages/create`, `messages/list`, `chats/list`).
- [ ] Add integration tests for REST + WS + Kafka + Redis path.
- [ ] Add load tests (k6/Locust) for:
  - [ ] burst writes
  - [ ] long chat history pagination
  - [ ] WS fanout to many recipients
- [ ] Define SLO targets and pass/fail criteria.

## 7) Documentation sync
- [ ] Update `.ai/knowledge/task.md` to current terms (`shard_id`, no `geo_scope`).
- [ ] Add scaling playbook (horizontal scaling, consumer scaling, partition tuning).
- [ ] Add runbook for incident scenarios (Redis down, Kafka lag, DB pressure, MinIO errors).
