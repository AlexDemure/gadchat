# TODO

## Data integrity
- [ ] Вернуть осмысленные DB constraints поверх текущей схемы.
- [ ] Добавить индексы под hot paths:
  - [ ] `member(user_id, chat_id)`
  - [ ] `member(user_id, position)`
  - [ ] `message(chat_id, created, id)`
  - [ ] `attachment(message_id, file_id)`
  - [ ] `read(message_id, member_id)`

## Performance
- [ ] Убрать N+1 в `chat.search(...)`.
- [ ] Убрать лишние `one(...)` внутри циклов там, где можно загрузить данные пачкой.
- [ ] Проверить `message.search(...)` и `chat.search(...)` на реальные индексы.

## Product features
- [ ] Редактирование сообщения.
- [ ] Soft delete сообщений.
- [ ] System messages как отдельный сценарий создания, а не только поле `kind`.
- [ ] Явное управление ролями в чате.
- [ ] Подготовить user/chat options под реальные настройки.

## Reliability
- [ ] Идемпотентность для `messages:create`.
- [ ] Retry / DLQ для Kafka consumer.
- [ ] Более безопасная схема согласования DB write + event publish.

## Realtime
- [ ] Проверить websocket flow под текущий JWT/user contract.
- [ ] Добавить ограничения и cleanup для долгоживущих соединений.

## Tests
- [ ] Unit tests для chat/message/file usecases.
- [ ] Integration tests для REST + Kafka + Redis + websocket пути.
- [ ] Проверить pinned chat position сценарии:
  - [ ] `position = 0`
  - [ ] `position = n`
  - [ ] `position = null`
- [ ] Проверить `messages:create` с `reply`, `forward`, `attachments`.
