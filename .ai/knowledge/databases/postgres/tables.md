# PostgreSQL Tables (Chat MVP)

## chat
Назначение: метаданные чата и ключи для масштабирования.

Поля:
- `id` (UUID, PK)
- `kind` (string, not null) — тип чата (`direct`, `group`, ...)
- `title` (string, nullable) — название чата (актуально для групп)
- `geo_scope` (string, not null, indexed) — гео-контур/регион чата
- `created` (timestamptz, not null)
- `shard_key` (bigint, not null, indexed) — детерминированный шард-ключ чата

## member
Назначение: участие пользователя в чате.

Поля:
- `id` (UUID, PK)
- `chat_id` (UUID, FK -> `chat.id`, on delete cascade, indexed)
- `user_id` (string, indexed)
- `created` (timestamptz, not null)

Ограничения:
- `UNIQUE(chat_id, user_id)` — один пользователь не может быть добавлен в один чат дважды.

## message
Назначение: сообщения внутри чата.

Поля:
- `id` (UUID, PK)
- `chat_id` (UUID, FK -> `chat.id`, on delete cascade, indexed)
- `member_id` (UUID, FK -> `member.id`, on delete cascade, indexed)
- `body` (string, nullable)
- `client_token` (string, nullable, indexed) — legacy поле для идемпотентности (в текущем task.md идемпотентность планируется через `message_id`)
- `created` (timestamptz, nullable)

## file
Назначение: универсальная сущность файла в объектном хранилище.

Поля:
- `id` (UUID, PK)
- `storage` (string, not null)
- `bucket` (string, not null, indexed)
- `key` (string, not null, indexed)
- `filename` (string, nullable)
- `content_type` (string, nullable)
- `size_bytes` (bigint, nullable)
- `created` (timestamptz, not null)

Ограничения:
- `UNIQUE(bucket, key)` — один и тот же объект в бакете хранится как одна запись.

## message_file
Назначение: связь many-to-many между `message` и `file` + порядок вложений.

Поля:
- `id` (UUID, PK)
- `message_id` (UUID, FK -> `message.id`, on delete cascade, indexed)
- `file_id` (UUID, FK -> `file.id`, on delete cascade, indexed)
- `position` (bigint, not null) — порядок вложения в сообщении
- `created` (timestamptz, not null)

## Связи
- `chat` 1 -> N `member`
- `chat` 1 -> N `message`
- `member` 1 -> N `message`
- `message` 1 -> N `message_file`
- `file` 1 -> N `message_file`

Эквивалентно:
- `message` N <-> N `file` через `message_file`.

## Правила целостности
- Удаление чата каскадно удаляет участников и сообщения.
- Удаление сообщения каскадно удаляет связи с вложениями (`message_file`).
- Удаление файла каскадно удаляет связи (`message_file`), но не сообщение.

## Примечание по развитию
- На текущий момент в БД есть `client_token` для legacy-дедупликации.
- В task.md выбран вектор на идемпотентность через заранее сгенерированный `message_id`.
- При финальной унификации схемы стоит либо:
  - убрать `client_token`, либо
  - явно зафиксировать, что поддерживаются оба механизма.
