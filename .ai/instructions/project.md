# Project Rules

## Boundaries
- Не изменять готовые модули без прямого запроса:
  - `src/infrastructure/databases/orm`
  - `src/infrastructure/monitoring`
  - `src/infrastructure/scheduling`
  - `src/framework`
  - `src/common`
- Новый код подстраивается под контракты этих модулей, а не меняет их.

## Layers
- `src/configuration` — настройки.
- `src/bootstrap` — composition root, lifecycle, запуск процессов.
- `src/entrypoints` — transport layer:
  - `http`
  - `websockets`
  - `workers`
  - `cron`
- `src/application` — usecases и доменные helper-утилиты.
- `src/infrastructure` — базы, брокеры, хранилища, CRUD/adapters.
- `src/static` — статика.

## HTTP
- В `entrypoints/http` только transport-логика и схемы.
- HTTP dependencies для usecases строятся через UoW в `src/entrypoints/http/common/uow/session.py`.
- Session должна закрываться до возврата ответа пользователю.
- Handler naming:
  - `query` — чтение
  - `command` — запись
- Если ручка возвращает pydantic-модель, указывать `response_model=...`.
- Если ручка ничего не возвращает или возвращает `Response`, указывать `response_class=Response`.
- `description` держать коротким, так как оно участвует в operation id:
  - `Create message`
  - `Search chats`
  - `Get file`
- Path ids в ручках принимать как `str = Path(...)`.
- Если usecase может поднять бизнес-ошибки, добавлять их в:
  - `responses={status.HTTP_401_UNAUTHORIZED: {}, **errors(...)}`

## Auth
- `POST /users:auth` принимает `x-user-id` и выдает JWT.
- Для защищенных public ручек использовать dependency `user`, а не строковый `jwt`, если usecase работает с доменным пользователем.
- Usecase `users/jwt.py`:
  - декодирует JWT
  - ищет `User` по `external_id`
  - если записи нет, поднимает `UserNotFound`
- `users/auth.py`:
  - создает `User`, если записи еще нет
  - возвращает JWT с `subject=user.id`

## Usecases
- Формат файла:
  - `Repository`
  - `Container`
  - `Usecase`
- В `Usecase` оставлять только:
  - `validate(...)`, если есть проверки
  - `__call__(...)`
- `validate(...)`:
  - ничего не возвращает
  - только проверяет инварианты и поднимает исключения
  - если нет await-вызовов, должна быть синхронной
- Не использовать `*` в сигнатурах функций.
- В usecase не писать ORM/SQL-запросы напрямую.
- В usecase запрещено импортировать FastAPI-слой.
- Использовать базовые методы репозиториев:
  - `exists(...)`
  - `one(...)`
  - `all(...)`
  - `create(...)`
  - `update(...)`
- Если объект не нужен дальше, не использовать `one(...)` только ради проверки существования:
  - использовать `exists(...)`
  - поднимать явную бизнес-ошибку `*NotFound`
- Если в `exists(...)` или `one(...)` нужно несколько фильтров, использовать `And.combine(...)`.
- Сложные запросы держать в CRUD:
  - `search(...)`
  - `direct(...)`
  - другие действительно query-heavy операции
- `one(...)` предполагается только там, где объект реально нужен для дальнейшей логики.

## Repository / CRUD
- Использовать `Repository`, не `Repositories`.
- В `Repository` хранить adapter-объекты, а не ORM-модели.
- CRUD слой:
  - не поднимает HTTP-ошибки
  - не содержит транспортной логики
  - по возможности придерживается правила `1 функция = 1 запрос`
- Если сценарий многошаговый, orchestration делается в usecase несколькими вызовами CRUD.
- В CRUD не тащить код из внешних слоев; использовать только database-related код и локальные postgres-модули.

## Chat Domain Model
- Каноничные таблицы:
  - `User`
  - `Role`
  - `Chat`
  - `Member`
  - `Message`
  - `Attachment`
  - `Reply`
  - `Forward`
  - `Read`
- Основной путь навигации:
  - `User -> Member -> Chat / Message`
- `Member` — участие пользователя в конкретном чате.
- В `Member` хранятся chat-scoped поля:
  - `role_id`
  - `position`
  - `notifications`
- `Message` — центральная сущность чата.
- `Reply` и `Forward` — отдельные m2m-таблицы между новым и исходным сообщением.
- `Attachment` связывает сообщение и заранее загруженный `File`.
- `Read` хранит факт прочтения сообщения участником.
- `Message.member_id` может быть `null` для системных сообщений.
- `Message.text` может быть `null`.

## Chat API Contracts
- Создание чата:
  - `POST /chats:create`
- Поиск чатов:
  - `POST /chats:search`
- Позиция чата:
  - `PATCH /chats/{chat_id}:position`
  - body содержит `position: int | None`
  - `null` снимает чат с pinned-позиции
- Сообщения:
  - `POST /chats/{chat_id}/messages:create`
  - `POST /chats/{chat_id}/messages:search`
  - `PUT /chats/{chat_id}/messages/{message_id}:read`
  - `PATCH /chats/{chat_id}/messages/{message_id}:pinned`
  - `DELETE /chats/{chat_id}/messages/{message_id}:pinned`
- Файлы:
  - `POST /chats/{chat_id}/files:upload:image`
  - `POST /chats/{chat_id}/files:upload:audio`
  - `POST /chats/{chat_id}/files:upload:document`
  - `POST /chats/{chat_id}/files:upload:video`
  - `GET /chats/{chat_id}/files/{file_id}`

## Files
- `File` хранит:
  - `path`
  - `filename`
  - `content_type`
  - `size`
  - `created`
- `storage`, `bucket`, `key`, `size_bytes` не используются.
- `File.serialize(...)` должен собирать готовый `url` для клиента.
- В upload-роутерах использовать общий helper `uploadfile(...)`.
- В upload-usecases принимать уже готовые:
  - `filename`
  - `content_type`
  - `content`

## Schemas
- Сериализация только в `entrypoints/http/.../schemas`.
- Имена запросных схем держать в едином стиле:
  - `Create*`
  - `Search*`
  - `Position*`
- Для search использовать множественное число:
  - `SearchChats`
  - `SearchMessages`
- Для response-коллекций:
  - `Chats`
  - `Messages`
- Для id полей в request-схемах использовать `StrRef`, если это ссылка на сущность.
- Не использовать `=""` как дефолт для строковых request-полей.
- Если текст опционален, использовать `String | None = None`, а не пустую строку.
- Если файлы сначала загружаются отдельно, в `CreateMessage.files` принимать только `list[StrRef]`.
- `CreateMessage.reply` и `CreateMessage.forward` оформлять как вложенные объекты.
- Для request-схем использовать `deserialize()`, если нужно преобразовать payload под usecase, а не делать `model_dump()` в роутере.

## Errors
- Бизнес-ошибки лежат в `src/application/collections/exceptions`.
- Бизнес-ошибки наследуются от `src.common.http.collections.HTTPError`.
- Не указывать `code` вручную для бизнес-ошибок.
- Для проверок наличия использовать специфичные ошибки:
  - `ChatNotFound`
  - `MemberNotFound`
  - `MessageNotFound`
  - `AttachmentNotFound`
  - `ReadNotFound`
  - `ReplyNotFound`
  - `ForwardNotFound`
  - `RoleNotFound`
  - `UserNotFound`
  - `FileNotFound`
- Для проверки доступа к чату использовать `UserNotMemberChat`.

## Naming and Imports
- Избегать alias-импортов вне `schemas`.
- В `__init__.py` не писать пустой `__all__`.
- Если ничего не экспортируется, `__all__` не нужен.
- Не делать типизацию при присваивании локальных атрибутов:
  - плохо: `self.jwt: JWT = jwt`
  - хорошо: `self.jwt = jwt`
- Для одноаргументных вызовов предпочитать named arguments:
  - `decode(token=token)`

## Data / Infra Rules
- Сессии использовать только через проектные deps/ORM context managers.
- В usecases и entrypoints не делать ручной `commit()` / `rollback()`.
- В upload-usecases:
  - сначала проверка membership
  - затем загрузка в MinIO
  - затем создание `File`
- В `messages:create`:
  - files — только ссылки на уже загруженные `File`
  - бизнес-правило: должно быть либо `text`, либо `files`
