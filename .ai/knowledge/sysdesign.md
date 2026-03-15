# Chat MVP System Design

## Контекст
- Сервис чата изолирован как blackbox.
- REST слой и WebSocket слой разделены по entrypoints:
  - `src/entrypoints/http` — REST API.
  - `src/entrypoints/websockets` — realtime stream (`/ws`).
- Синхронизация realtime между pod-ами идет через Redis Pub/Sub.
- Асинхронный ingest путь для масштабирования записи идет через Kafka + отдельный worker.
- Хранение данных: Postgres (ORM + миграции).

## Компоненты и связи
```mermaid
flowchart LR
    U[Клиентское приложение]
    API[HTTP API сервиса чата]
    WS[WebSocket endpoint сервиса]
    MGR[Менеджер активных WS-подключений]
    WL[Фоновый worker подписки на Redis]
    REDIS[(Redis Pub/Sub)]
    KAFKA[(Kafka)]
    WK[Worker обработки входящих событий]
    DB[(Postgres)]
    S3[(MinIO)]

    U -->|Отправляет REST-запросы на чтение и запись| API
    U -->|Открывает постоянное WS-соединение для realtime| WS
    WS -->|Регистрирует соединение пользователя| MGR

    API -->|Читает и пишет чаты и сообщения| DB
    API -->|Сохраняет метаданные вложений| DB
    API -->|Сохраняет бинарные файлы вложений| S3

    API -->|Публикует событие нового сообщения для асинхронной обработки| KAFKA
    KAFKA -->|Передает событие consumer-воркеру| WK
    WK -->|Сохраняет результат обработки в БД| DB
    WK -->|Публикует событие доставки для онлайн-клиентов| REDIS

    REDIS -->|Отдает события подписанному listener-воркеру| WL
    WL -->|Передает событие в менеджер подключений для fanout| MGR
    MGR -->|Доставляет событие в активные WS-клиенты адресатов| U

    API -.->|Fallback: отправляет в WS напрямую если Kafka и Redis отключены| MGR
```

## Поток отправки сообщения
```mermaid
sequenceDiagram
    participant C as Клиент
    participant H as HTTP ручка POST messages
    participant K as Kafka
    participant W as Worker ingest
    participant P as Postgres
    participant R as Redis Pub/Sub
    participant S as Менеджер WS-подключений
    participant C2 as Клиент-получатель

    C->>H: Отправляет сообщение и данные автора
    alt Включена Kafka
        H->>K: Кладет событие сообщения в очередь
        H-->>C: Быстро возвращает статус accepted
        K->>W: Воркер получает событие из топика
        W->>P: Создает или находит чат, сохраняет сообщение
        W->>R: Публикует событие message.created для доставки
        R->>S: Listener получает событие и отдает в WS-менеджер
        S-->>C2: Получатель мгновенно видит сообщение в открытом чате
    else Kafka отключена (синхронный путь)
        H->>P: Сохраняет сообщение сразу в запросе
        alt Включен Redis
            H->>R: Публикует событие доставки
            R->>S: Listener передает событие в WS-менеджер
            S-->>C2: Получатель получает realtime-обновление
        else Redis отключен
            H->>S: Вызывает прямую доставку через manager.send_to_users
            S-->>C2: Получатель получает событие напрямую
        end
        H-->>C: Возвращает persisted и сохраненное сообщение
    end
```

## Поток синхронизации и чтения
```mermaid
sequenceDiagram
    participant C as Клиент
    participant API as HTTP API
    participant DB as Postgres
    participant WS as WS канал

    C->>API: Запрашивает список чатов пользователя
    API->>DB: Читает чаты, участников и превью последних сообщений
    DB-->>API: Возвращает данные списка чатов
    API-->>C: Отдает страницу списка чатов

    C->>API: Запрашивает часть истории чата по cursor и direction
    API->>DB: Читает порцию сообщений с курсорной пагинацией
    DB-->>API: Возвращает items и курсоры prev/next
    API-->>C: Отдает chunk для двунаправленного бесконечного списка

    Note over WS,C: Онлайн-пользователь получает новые сообщения мгновенно по WS
    Note over API,C: После перезахода клиент добирает пропущенные сообщения через REST-пагинацию
```

## Синхронизация между pod-ами
```mermaid
flowchart TB
    subgraph Pod A
        APIA[HTTP API в pod A]
        WSA[WS менеджер в pod A]
        LA[Redis listener в pod A]
    end

    subgraph Pod B
        APIB[HTTP API в pod B]
        WSB[WS менеджер в pod B]
        LB[Redis listener в pod B]
    end

    REDIS[(Redis Pub/Sub)]

    APIA -->|Публикует событие о новом сообщении| REDIS
    APIB -->|Публикует событие о новом сообщении| REDIS
    REDIS -->|Рассылает событие всем подписчикам| LA
    REDIS -->|Рассылает событие всем подписчикам| LB
    LA -->|Передает событие локальным WS-соединениям| WSA
    LB -->|Передает событие локальным WS-соединениям| WSB
```

## Гео и масштабирование
- Горизонтальное масштабирование: любой pod может принять REST/WS подключение.
- Realtime fanout: через Redis Pub/Sub события доходят до WS manager каждого pod-а.
- Geo-scope хранится в доменных сущностях сообщений/чатов и может использоваться для geo-routing.
- Kafka ingress decouples API latency от тяжелого пути записи под нагрузкой.

## Инварианты и границы
- Авторизация в MVP: `x-user-id` из токена/шлюза (само auth не реализуется в сервисе).
- Дедупликация может быть расширена через idempotency token (в MVP упрощена).
- ORM-модели используются внутри приложения; сериализация только на уровне `schemas`.
- `bootstrap` не содержит бизнес-логики: только composition root и lifecycle.
