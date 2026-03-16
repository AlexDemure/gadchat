# Architecture

## Карта слоев
- `src/configuration` — настройки окружения.
- `src/bootstrap` — composition root, lifecycle, запуск процессов.
- `src/entrypoints` — входные точки транспорта (`http`, `websockets`, `workers`, `cron`).
- `src/application` — бизнес-оркестрация (`usecases`) и доменные helper-функции (`utils`).
- `src/infrastructure` — БД, брокеры, хранилища, ORM/CRUD-адаптеры.
- `src/static` — статика и demo HTML.

## Configuration layer (`src/configuration`)
- Все настройки описываются в `src/configuration/setup.py` через `BaseSettings`.
- Используется агрегирующий класс `Settings(*configs)`.
- Импорт в приложении только через `from src.configuration import settings`.
- Имена env-полей: uppercase + subsystem prefix (`POSTGRES_*`, `REDIS_*`, `KAFKA_*`, `MINIO_*`).

## Bootstrap layer (`src/bootstrap`)
- `server.py`:
  - поднимает инфраструктуру (`postgres.start()`, `redis.start()`, `minio.start()`, `kafka.start()`),
  - запускает фоновые задачи через `workers()` + `background.start()`,
  - подключает `http.router` и `websockets.router`,
  - завершает ресурсы в shutdown в обратном порядке.
- `worker.py`:
  - отдельный процесс ingest-консьюмера Kafka,
  - вызывает application usecase,
  - публикует delivery-event в Redis.
- В `bootstrap` запрещена доменная логика: только orchestration/lifecycle.

## Entrypoints layer (`src/entrypoints`)

### HTTP (`src/entrypoints/http`)
- Только REST endpoints.
- Структура:
  - `common`: общие deps/константы/схемы,
  - `public`: пользовательские ручки + deps + schemas,
  - `system`: системные ручки (например health).
- В `public` домены раскладываются по namespace:
  - `routers/users/*` для auth/user-level операций
  - `routers/chats/*` для chat-level операций
  - вложенные ресурсы: `routers/chats/messages/*`, `routers/chats/files/*`
- Router assembly через `registry.py` на каждом уровне.
- Handler naming:
  - `query` — операции чтения,
  - `command` — операции записи.
- HTTP handler:
  - принимает/валидирует вход,
  - вызывает usecase,
  - сериализует через schema.

### WebSockets (`src/entrypoints/websockets`)
- Только WS endpoints (`/ws`) и realtime-логика.
- `manager.py` хранит активные подключения и доставляет события адресатам.
- Аутентификация WS — тем же application JWT, что и REST.
- Входящие write-операции через WS в MVP не выполняются (write через REST).

### Workers (`src/entrypoints/workers`)
- Фоновые задачи API-процесса.
- Регистрация задач в `registry.py` через `background.add(...)`.
- Текущая задача: Redis listener, который читает pub/sub и делает fanout в `ConnectionManager`.

### Cron (`src/entrypoints/cron`)
- Каркас для периодических задач.
- Cron-задачи вызывают usecases, не содержат transport/API serialization.

## Application layer (`src/application`)

### Usecases (`src/application/usecases`)
- Формат: `src/application/usecases/<domain>/<resource>/<action>.py`.
- Правило: `1 файл = 1 бизнес-операция`.
- Имена action-файлов должны отражать контракт ручки:
  - `search.py`, `create.py`, `get.py`, `auth.py`
- Шаблон файла:
  - `Repositories`
  - `Security`
  - `Container`
  - `Usecase`
- Usecase оркестрирует репозитории/инфраструктуру, но не transport.
- Для auth-декодирования пользователя используется отдельный usecase `users/get.py`.
- Для chat-scoped usecase-ов membership-проверка инкапсулируется в `validate(...)` внутри usecase.

### Utils (`src/application/utils`)
- Повторно используемые доменные helper-функции.
- Не содержат SQL/ORM orchestration и transport-код.
- Используются для cursor logic, payload normalization, небольших трансформаций.

## Infrastructure layer (`src/infrastructure`)

### Общая структура
- Интеграции разделены по категориям:
  - `databases`
  - `storages`
  - `brokers`
- Для модуля интеграции используются `client.py`, `setup.py`, `collections/*`, `__init__.py`.

### Database access
- Postgres клиент поднимается через `postgres.start()`.
- Сессии только через контексты ORM:
  - `async with postgres.orm.read() as session`
  - `async with postgres.orm.write() as session`
- Внутри `write()` уже открыт `session.begin()`, поэтому:
  - не вызывать `session.commit()`/`session.rollback()` вручную в usecases/handlers.

### Postgres tables/CRUD
- Таблицы: `src/infrastructure/databases/postgres/tables`.
- CRUD: `src/infrastructure/databases/postgres/crud`.
- Табличные модели и CRUD-классы именуются в singular.
- CRUD слой работает с ORM-моделями и query builders, без API-сериализации.

## Данные и синхронизация (текущая реализация)
- Auth flow:
  - `POST /users:auth` принимает `x-user-id`
  - возвращает application JWT
  - REST использует `Authorization: Bearer <token>`
  - WS использует тот же токен в query (`/ws?token=...`)
- Создание сообщения:
  - REST `POST /chats/{chat_id}/messages:create` -> Kafka ingress async path
- Persist:
  - usecase создает/находит чат, сохраняет message и attachments.
- Realtime delivery:
  - через Redis pub/sub -> worker listener -> WS connection manager -> клиенты.
- История и список чатов:
  - читаются только через REST с `POST ...:search` и cursor-пагинацией.
- Вложения:
  - загружаются через `POST /chats/{chat_id}/files:upload:<kind>`
  - читаются через `GET /chats/{chat_id}/files/{file_id}`

## Обязательные границы
- Сериализация только в `entrypoints/.../schemas`.
- Usecase/CRUD не должны знать о FastAPI response-моделях.
- `bootstrap` не содержит бизнес-правил.
- WS и HTTP разделены по разным entrypoints.
- Глобальные mutable state-объекты для сессий/движка запрещены.
- HTTP dependency не должна содержать доменную бизнес-логику:
  - извлечение bearer token в dependency допустимо,
  - декодирование и получение `user_id` выполняется через usecase.
# Architecture

## Chat Domain Canonical Schema
- Каноничная chat-схема берется из `src/infrastructure/databases/postgres/tables/chat.py`, `user.py`, `role.py`, `file.py`.
- Основной путь навигации по домену чата:
  - `User -> Member -> Message`
  - через `Member` пользователь получает свои чаты, а дальше уже сообщения и остальные связи.
- `Member` это участие пользователя в конкретном чате, а не глобальный профиль пользователя.
- В `Member` хранятся chat-scoped поля:
  - `position` — pin-позиция чата для пользователя
  - `notifications` — количество непрочитанных/необработанных уведомлений по чату
- `Message` является центральной сущностью для reply/forward/read/attachment.
- `Reply` и `Forward` — отдельные m2m-таблицы, каждая связывает:
  - новое сообщение
  - исходное сообщение
- В `Reply` и `Forward` не дублируется `chat_id`, если чат можно получить через связанное `Message`.
- Из `Message` доступны:
  - `reply`
  - `forward`
  - `attachments`
  - `member`
  - `user`
- При реализации кода под chat-домен нужно подстраиваться под эту схему, а не перестраивать таблицы под старую модель.
