from src.application.protocols import commands
from src.application.protocols import domain
from src.application.protocols import events
from src.application.protocols import transport
from src.common.formats.utils import date
from src.common.formats.utils import uuid
from src.decorators import sessionmaker
from src.domain.collections import MessageKind
from src.infrastructure.brokers.collections import EventKind
from src.infrastructure.brokers.collections import EventStatus
from src.infrastructure.brokers.collections import Topic
from src.infrastructure.brokers.kafka import kafka
from src.infrastructure.databases.orm.sqlalchemy.queries import Filter
from src.infrastructure.databases.orm.sqlalchemy.session import Session
from src.infrastructure.databases.postgres import adapters


class Repository:
    def __init__(self, session: Session) -> None:
        self.role = adapters.repositories.Role(session)
        self.user = adapters.repositories.User(session)
        self.chat = adapters.repositories.Chat(session)
        self.member = adapters.repositories.Member(session)
        self.message = adapters.repositories.Message(session)


class Broker:
    def __init__(self) -> None:
        self.kafka = kafka


class Container:
    def __init__(self, repository: Repository, broker: Broker) -> None:
        self.repository = repository
        self.broker = broker


class Usecase:
    def __init__(self) -> None:
        self.container = None

    def build(self, session: Session) -> None:
        self.container = Container(repository=Repository(session), broker=Broker())

    @sessionmaker.write
    async def execute(self, session: Session, command: commands.CreateChat) -> None:
        self.build(session)

        payload = command.payload

        user = await self.container.repository.user.one(Filter.eq(key="id", value=command.user_id))

        admin = await self.container.repository.role.one(Filter.eq(key="id", value="admin"))
        customer = await self.container.repository.role.one(Filter.eq(key="id", value="customer"))

        created = date.now()

        chat = await self.container.repository.chat.create(
            {
                "id": uuid.unique(),
                "title": payload.title,
                "options": {},
                "created": created,
            },
        )

        await self.container.repository.member.create(
            {
                "id": uuid.unique(),
                "chat_id": chat.id,
                "user_id": user.id,
                "role_id": admin.id,
                "position": None,
                "notifications": 0,
            }
        )

        for user_id in payload.user_ids:
            await self.container.repository.member.create(
                {
                    "id": uuid.unique(),
                    "chat_id": chat.id,
                    "user_id": user_id,
                    "role_id": customer.id,
                    "position": None,
                    "notifications": 0,
                }
            )

        await self.container.repository.message.create(
            {
                "id": uuid.unique(),
                "chat_id": chat.id,
                "user_id": None,
                "member_id": None,
                "kind": MessageKind.system.value,
                "text": "Канал создан",
                "created": created,
            }
        )

        chat = await self.container.repository.chat.relations(Filter.eq(key="id", value=chat.id))

        await self.container.broker.kafka.publish(
            events.CreateChat(
                request_id=command.request_id,
                kind=EventKind.event,
                status=EventStatus.completed,
                topic=Topic.chat_create,
                targets=transport.Event.Targets(user_ids=[command.user_id, *payload.user_ids]),
                payload=payload,
                response=events.CreateChat.Response(chat=domain.Chat.serialize(user, chat)),
                error=None,
            ).model_dump(mode="json"),
            topic=Topic.chat_create.event,
        )
