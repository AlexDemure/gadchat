# PostgreSQL Tables

## user
Назначение: глобальная сущность пользователя для auth и связей в chat-domain.

Поля:
- `id`
- `external_id`
- `authorization`
- `options`

## role
Назначение: справочник ролей участника чата.

Поля:
- `id`
- `name`

## chat
Назначение: корневая сущность чата.

Поля:
- `id`
- `title`
- `created`
- `options`

## member
Назначение: участие пользователя в конкретном чате.

Поля:
- `id`
- `chat_id`
- `user_id`
- `role_id`
- `position`
- `notifications`

Смысл:
- `position` — pinned-позиция чата для пользователя
- `notifications` — число непрочитанных/необработанных уведомлений по чату

## message
Назначение: сообщение внутри чата.

Поля:
- `id`
- `chat_id`
- `user_id`
- `member_id`
- `kind`
- `text`
- `pinned`
- `edited`
- `created`

Примечания:
- `user_id` и `member_id` могут быть `null` для системных сообщений
- `text` может быть `null`

## file
Назначение: метаданные файла в объектном хранилище.

Поля:
- `id`
- `path`
- `filename`
- `content_type`
- `size`
- `created`

## attachment
Назначение: связь сообщения с загруженным файлом.

Поля:
- `id`
- `message_id`
- `file_id`

## reply
Назначение: связь нового сообщения с сообщением-источником для reply.

Поля:
- `id`
- `message_id`
- `source_message_id`

## forward
Назначение: связь нового сообщения с сообщением-источником для forward.

Поля:
- `id`
- `message_id`
- `source_message_id`

## read
Назначение: факт прочтения сообщения участником.

Поля:
- `id`
- `message_id`
- `member_id`
- `created`

## Current Relations
- `chat` 1 -> N `member`
- `chat` 1 -> N `message`
- `user` 1 -> N `member`
- `user` 1 -> N `message`
- `role` 1 -> N `member`
- `member` 1 -> N `message`
- `message` 1 -> N `attachment`
- `file` 1 -> N `attachment`
- `message` 1 -> 0..1 `reply`
- `message` 1 -> 0..1 `forward`
- `message` 1 -> N `read`

## Notes
- В текущем состоянии project intentionally ослабил часть DB-level защиты, поэтому knowledge должен считаться source of intent, а не полного набора constraints.
- Для pinned chat position используется `member.position`, а не отдельная таблица.
- Для pinned message используется `message.pinned`, а не отдельная таблица.
- `file.path` хранится без домена, например `/chats/{chat_id}/{type}/{file_id}.{ext}`.
- В ORM `Message` использует read-only proxy-поля:
  - `attachments -> File[]`
  - `reply -> Message | None`
  - `forward -> Message | None`
- В read-path для message search `Read` загружается персонально для текущего `member`.
