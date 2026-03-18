# Current Task Context

## Goal
- Поддерживать chat-service как набор сервисов `gateway`, `core`, `auth`, `uploader`.
- Код и база знаний должны соответствовать текущей модели данных и актуальному разделению:
  - `gateway` -> websocket commands / Kafka edge / realtime delivery
  - `core` -> REST queries / snapshots
  - chat processor -> Kafka consumer / write-side / domain events

## Current Auth Model
- `POST /users:auth` принимает `x-user-id`.
- Сервис создает `User`, если записи еще нет.
- В ответ возвращается JWT.
- `GET /users:current` возвращает текущего пользователя по JWT.
- Остальные public ручки работают через `Authorization: Bearer <token>`.
- Dependency `user` возвращает ORM `User` из БД.

## Current Chat Model
- Каноничные сущности:
  - `User`
  - `Role`
  - `Chat`
  - `Member`
  - `Message`
  - `Attachment`
  - `Reply`
  - `Forward`
  - `Read`
- `Member` хранит:
  - принадлежность пользователя к чату
  - `role_id`
  - `position`
  - `notifications`
- `Message` может быть системным, поэтому `member_id` и `user_id` могут быть `null`.
- `Attachment` связывает сообщение с заранее загруженным `File`.
- `Reply` и `Forward` — отдельные связи на исходное сообщение.

## Current API
- Gateway websocket command topics:
  - `chat.create.command`
  - `chat.position.command`
  - `message.create.command`
  - `message.read.command`
  - `message.pinned.command`
  - `message.unpinned.command`
- Gateway protocol HTTP docs mirror websocket topics as `POST` routes with `response_model=Event`.
- Core REST:
  - `POST /chats:search`
  - `POST /chats/{chat_id}/messages:search`
- Uploader REST:
  - `POST /api/files:image`
  - `POST /api/files:audio`
  - `POST /api/files:document`
  - `POST /api/files:video`

## Important Current Rules
- Search и snapshot остаются в `core`, а не в `gateway`.
- Gateway protocol handlers используют только `POST`.
- Gateway protocol schemas используют поле `topic`, например `message.create.command`.
- Gateway protocol handlers возвращают `Event.mock(...)` для OpenAPI / docs слоя.
- `CreateMessage` в gateway строится через базовый `Message`.
- Внутренние вложенные request-схемы для `CreateMessage` называются:
  - `CreateMessageReply`
  - `CreateMessageForward`
- В `uploader` строго используем единый стиль:
  - router param: `usecase: Usecase = Depends(dependency)`
  - deps imports: `Container`, `Repository`, `Storage`, `Usecase`

## Current Refactor Direction
- Gateway больше не должен писать command outbox в Postgres как основной intake path.
- Gateway должен:
  - публиковать command в Kafka
  - сразу отдавать transport ack
  - читать domain events из Kafka
  - доставлять их в websocket clients
- Начинаем с потока `chat.create`.
