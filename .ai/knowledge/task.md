# Current Task Context

## Goal
- Поддерживать chat-service как отдельный модуль с REST и websocket.
- Код и база знаний должны соответствовать текущей модели данных и текущим HTTP-контрактам, а не старым MVP-идеям.

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
- Users:
  - `POST /users:auth`
  - `GET /users:current`
- Chats:
  - `POST /chats:create`
  - `POST /chats:search`
  - `PATCH /chats/{chat_id}:position`
- Messages:
  - `POST /chats/{chat_id}/messages:create`
  - `POST /chats/{chat_id}/messages:search`
  - `PUT /chats/{chat_id}/messages/{message_id}:read`
  - `PATCH /chats/{chat_id}/messages/{message_id}:pinned`
  - `DELETE /chats/{chat_id}/messages/{message_id}:pinned`
- Files:
  - `POST /chats/{chat_id}/files:upload:image`
  - `POST /chats/{chat_id}/files:upload:audio`
  - `POST /chats/{chat_id}/files:upload:document`
  - `POST /chats/{chat_id}/files:upload:video`
  - `GET /chats/{chat_id}/files/{file_id}`

## Important Current Rules
- `messages:create` принимает:
  - `text: String | None`
  - `reply` как объект с `message`
  - `forward` как объект с `chat` и `message`
  - `files` как список `file_id`
- Сначала файл загружается отдельной ручкой, потом его `id` используется в `messages:create`.
- В usecase допускаются только `validate()` и `__call__()`.
- Для проверок существования использовать `exists()` и поднимать доменные ошибки, если объект дальше не нужен.
- HTTP deps usecases собираются через `UsecaseRunner` в `src/entrypoints/http/common/helpers/usecases/runner.py`.
- `chats:search` и `messages:search` больше не принимают `sorting` в публичном контракте.
- `chat.search(...)`:
  - без `user_id` отдает общий список чатов по `created desc, id desc`
  - с `user_id` использует персональную логику по `member.position` и `last activity`
- `message.search(...)` всегда отдает историю по `message.created desc, message.id desc`.
- В response-схемах сообщений:
  - `attachments` отдаются сразу как `File[]`
  - `reply` и `forward` отдаются как одноуровневые вложенные сообщения
  - `read` персонализирован и зависит от текущего `member`
