# Code Style

## Общие принципы
- Бизнес-логика живет в `src/application/usecases`.
- Входные точки (`HTTP`, `worker`, `cron`) живут в `src/entrypoints`.
- `bootstrap` отвечает только за composition root, lifecycle и запуск процесса.
- CRUD/репозитории работают с ORM-моделями и не сериализуют данные в API-форматы.

## Naming
- Для HTTP handlers:
  - `query` для операций чтения (`GET`, `WebSocket read/stream`).
  - `command` для операций записи (`POST`, `PUT`, `PATCH`, `DELETE`).
- `1 файл = 1 бизнес-операция` в `usecases`.
- Python-файлы action-level usecase/deps/router именуются по операции, а не по абстрактной сущности:
  - корректно: `search.py`, `create.py`, `get.py`, `auth.py`, `image.py`, `video.py`.
  - некорректно: `list.py`, если ручка фактически обслуживает `:search`.
- Имя файла должно совпадать с контрактом ручки:
  - `POST ...:search` -> `search.py`
  - `POST ...:create` -> `create.py`
  - `GET .../{id}` -> `get.py`
  - `POST ...:auth` -> `auth.py`
- Для модульных сборок (`registry.py`) импортировать одноимённые action-модули:
  - `from . import search`
  - `from . import create`

## Imports
- Не использовать alias-импорты (`as ...`) в `application`, `entrypoints`, `bootstrap`, `infrastructure`.
- Alias допустим только в `schemas`, когда нужно подчеркнуть ORM-тип во входе `serialize(...)`.
- Предпочитать явные, прямые импорты без переименования символов.
- В `__init__.py` не размещать исполняемый код, константы, функции или классы.
- `__init__.py` используется только для импортов и сборки `__all__`.
- Стандартную библиотеку импортировать в модульном стиле:
  - корректно: `import datetime`, `import typing`, `import collections`.
  - некорректно: `from datetime import datetime`, `from typing import Any`.
- Внешние библиотеки импортировать точечно по компонентам:
  - `from fastapi import FastAPI`
  - `from sqlalchemy import select`
- Для сборки модулей (например `registry.py`) использовать модульные локальные импорты:
  - `from . import search`
  - `from . import create`
  - `router.include_router(search.router)`

## Auth and HTTP deps
- `Depends(jwt)` в HTTP не разбирает header вручную.
- Для Bearer auth использовать `fastapi.security.HTTPBearer`:
  - dependency принимает `HTTPAuthorizationCredentials`
  - дальше в usecase передаётся `authorization.credentials`
- Dependency `jwt` отвечает только за извлечение bearer credentials и вызов usecase декодирования.
- Header-based dependency `header` используется только для ручки выдачи токена (`POST /users:auth`).
- Для публичных chat-ручек:
  - `POST /users:auth` принимает `x-user-id`
  - остальные chat REST-ручки принимают `Authorization: Bearer <token>`

## Usecases
- Структура файла usecase:
  - `Repositories`
  - `Security`
  - `Container`
  - `Usecase`
- Usecase должен оркестрировать зависимости, а не заниматься transport-логикой.
- Usecase не должен собирать и выполнять ORM/SQL-запросы напрямую.
- Usecase не должен хранить ссылки на ORM-модели в `Repositories`.
- В `Repositories` должны лежать ссылки на CRUD-объекты, через которые и выполняется доступ к данным.
- Вызовы из usecase должны идти через `self.container.repositories.*`:
  - корректно: `await self.container.repositories.chat.search(filters, sorting, pagination)`
  - некорректно: `session.get(Model, id)`, `select(...)`, `queries.Filter.eq(...)` внутри usecase
- В usecase в репозиторий прокидываются входные Python-объекты и структуры фильтрации:
  - `filters`
  - `sorting`
  - `pagination`
  - `dict`, `list`, scalar values и другие подготовленные аргументы
- Если операция работает с `chat_id`, usecase обязан иметь `validate(...)` для проверки членства пользователя в чате.
- Проверка членства не должна жить в HTTP router.
- Декодирование application JWT также оформляется отдельным usecase (`users/get.py`), а не выполняется прямо в dependency.

## Schemas
- Сериализация ответа делается только в `schemas`.
- Методы сериализации принимают ORM-модели и возвращают schema-модели (`serialize(...)`).
- Для одного домена схемы группируются в один файл (например `public/schemas/chat.py`).
- Naming схем:
  - `Search*` для поисковых запросов
  - `Create*` для создания
  - `Update*` для изменения
  - `Delete*` для удаления
- Пагинируемые response-схемы называть во множественном числе:
  - `Chats`, `Messages`
- Item-схемы внутри `items` называть в единственном числе:
  - `Chat`, `Message`

## EntryPoints / REST structure
- Поддерживать REST-древо по директориям в `entrypoints/http/public`:
  - `routers/chats/*`
  - `routers/chats/messages/*`
  - `routers/chats/files/*`
  - `routers/users/*`
- Избегать дублирующих уровней вроде `chats/chats`.
- WebSocket endpoint-ы выносить из `http` в отдельный entrypoint `src/entrypoints/websockets`.
- В `http` оставлять только REST endpoint-ы.
- User-scoped auth endpoint размещать в `routers/users/auth.py`, а не внутри `routers/chats`.
- Для chat API придерживаться action-style REST контрактов:
  - `POST /chats:search`
  - `POST /chats:create`
  - `POST /chats/{chat_id}/messages:search`
  - `POST /chats/{chat_id}/messages:create`
  - `POST /chats/{chat_id}/files:upload:image`
  - `GET /chats/{chat_id}/files/{file_id}`

## Database access
- Запрещено хранить session factory/engine в глобальных переменных модуля и в `app.state` для бизнес-зависимостей.
- Сессии получать только через инфраструктурный ORM-контекст:
  - read: `async with postgres.orm.read() as session`
  - write: `async with postgres.orm.write() as session`
- Внутри `postgres.orm.write()` запрещено вручную вызывать `session.commit()` и `session.rollback()` в usecase/entrypoints.
- В HTTP deps:
  - read usecase подключать через `Depends(read)`,
  - write usecase подключать через `Depends(write)`.

## Background workers
- Фоновые задачи процесса API регистрировать в `src/entrypoints/workers` через `background.add(...)`.
- В `bootstrap/server.py` запускать только orchestration:
  - `workers()`
  - `background.start()`
  - `background.shutdown()`
- Реализацию фоновых корутин (например Redis listener) держать в `entrypoints/workers/*`, а не в `bootstrap`.

## Static
- HTML и статические ресурсы хранить в `src/static`.
- Раздача статики через mount приложения (`/api/static`).

## Errors and validation
- Валидацию входа делать на границе (`schemas` + handler checks).
- Доменные ошибки и инварианты проверять в usecase.
- Не прятать исключения без необходимости.
- Для JWT-защищённых HTTP ручек указывать:
  - `responses={status.HTTP_401_UNAUTHORIZED: {}, **errors(*AUTHORIZATION_ERRORS)}`
- Для `POST /users:auth` указывать:
  - `responses={status.HTTP_401_UNAUTHORIZED: {}}`

## Date and JSON utils
- Для получения текущего времени использовать проектный helper `src.common.formats.utils.date.now()`.
- Если в модуле импортирован `src.common.formats.utils.json`, сериализацию/десериализацию делать через:
  - `json.tostring(...)`
  - `json.fromstring(...)`
- Не использовать у этого helper-модуля вызовы стандартного API вида `json.dumps(...)`/`json.loads(...)`.
