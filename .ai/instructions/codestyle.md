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
- Python-файлы (`*.py`) именуются в единственном числе по сущности:
  - корректно: `chat.py`, `message.py`, `ticket.py`.
- Исключения допустимы, если имя в единственном числе конфликтует с библиотекой/модулем или ухудшает читаемость:
  - в таких случаях допускается сокращение или множественное число.

## Imports
- Не использовать alias-импорты (`as ...`) в `application`, `entrypoints`, `bootstrap`, `infrastructure`.
- Alias допустим только в `schemas`, когда нужно подчеркнуть ORM-тип во входе `serialize(...)`.
- Предпочитать явные, прямые импорты без переименования символов.
- Стандартную библиотеку импортировать в модульном стиле:
  - корректно: `import datetime`, `import typing`, `import collections`.
  - некорректно: `from datetime import datetime`, `from typing import Any`.
- Внешние библиотеки импортировать точечно по компонентам:
  - `from fastapi import FastAPI`
  - `from sqlalchemy import select`
- Для сборки модулей (например `registry.py`) использовать модульные локальные импорты:
  - `from . import demo`
  - `from . import list`
  - `router.include_router(demo.router)`

## Usecases
- Структура файла usecase:
  - `Repositories`
  - `Security`
  - `Container`
  - `Usecase`
- Usecase должен оркестрировать зависимости, а не заниматься transport-логикой.

## Schemas
- Сериализация ответа делается только в `schemas`.
- Методы сериализации принимают ORM-модели и возвращают schema-модели (`serialize(...)`).
- Для одного домена схемы группируются в один файл (например `public/schemas/chat.py`).

## EntryPoints / REST structure
- Поддерживать REST-древо по директориям в `entrypoints/http/public`:
  - `routers/chats/*`
  - `routers/chats/messages/*`
  - `routers/chats/ws/*`
- Избегать дублирующих уровней вроде `chats/chats`.
- WebSocket endpoint-ы выносить из `http` в отдельный entrypoint `src/entrypoints/websockets`.
- В `http` оставлять только REST endpoint-ы (включая вспомогательные REST точки для WS, например ticket-issue).

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

## Date and JSON utils
- Для получения текущего времени использовать проектный helper `src.common.formats.utils.date.now()`.
- Если в модуле импортирован `src.common.formats.utils.json`, сериализацию/десериализацию делать через:
  - `json.tostring(...)`
  - `json.fromstring(...)`
- Не использовать у этого helper-модуля вызовы стандартного API вида `json.dumps(...)`/`json.loads(...)`.
