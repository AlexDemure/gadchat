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
from src.infrastructure.databases.orm.sqlalchemy.queries import And
from src.infrastructure.databases.orm.sqlalchemy.queries import Filter
from src.infrastructure.databases.orm.sqlalchemy.session import Session
from src.infrastructure.databases.postgres import adapters


class Repository:
    def __init__(self, session: Session) -> None:
        self.user = adapters.repositories.User(session)
        self.chat = adapters.repositories.Chat(session)
        self.file = adapters.repositories.File(session)
        self.member = adapters.repositories.Member(session)
        self.message = adapters.repositories.Message(session)
        self.attachment = adapters.repositories.Attachment(session)
        self.forward = adapters.repositories.Forward(session)
        self.reply = adapters.repositories.Reply(session)


class Broker:
    def __init__(self) -> None:
        self.kafka = kafka


class Container:
    def __init__(self, repository: Repository, broker: Broker) -> None:
        self.repository = repository
        self.broker = broker


class Usecase:
    def __init__(self) -> None:
        self.container: Container | None = None

    def build(self, session: Session) -> None:
        self.container = Container(repository=Repository(session), broker=Broker())

    @sessionmaker.write
    async def execute(
        self,
        session: Session,
        command: commands.CreateMessage,
    ) -> None:
        self.build(session)

        payload = command.payload

        user = await self.container.repository.user.one(Filter.eq(key="id", value=command.user_id))

        chat = await self.container.repository.chat.one(Filter.eq(key="id", value=payload.chat_id))

        member = await self.container.repository.member.one(
            And.combine(
                Filter.eq(key="chat_id", value=chat.id),
                Filter.eq(key="user_id", value=user.id),
            )
        )

        message = await self.container.repository.message.create(
            {
                "id": uuid.unique(),
                "chat_id": chat.id,
                "user_id": user.id,
                "member_id": member.id,
                "kind": MessageKind.user,
                "text": payload.text,
                "pinned": None,
                "edited": None,
                "created": date.now(),
            },
        )

        for file_id in payload.file_ids:
            await self.container.repository.attachment.create(
                {
                    "id": uuid.unique(),
                    "message_id": message.id,
                    "file_id": file_id,
                },
            )

        if payload.reply:
            await self.container.repository.reply.create(
                {
                    "id": uuid.unique(),
                    "message_id": message.id,
                    "source_message_id": payload.reply.message_id,
                    "created": date.now(),
                },
            )

        if payload.forward:
            await self.container.repository.forward.create(
                {
                    "id": uuid.unique(),
                    "message_id": message.id,
                    "source_message_id": payload.forward.message_id,
                    "created": date.now(),
                },
            )

        members = await self.container.repository.member.all(Filter.eq(key="chat_id", value=chat.id))

        for _member in members:
            if _member.id != member.id:
                await self.container.repository.member.update(id=_member.id, notifications=_member.notifications + 1)

        message = await self.container.repository.message.relations(Filter.eq(key="id", value=message.id))

        targets = [item.user_id for item in members]

        targets.append(member.id)

        await self.container.broker.kafka.publish(
            events.CreateMessage(
                request_id=command.request_id,
                kind=EventKind.event,
                status=EventStatus.completed,
                topic=Topic.chat_message_create,
                targets=transport.Event.Targets(users=targets),
                payload=payload,
                response=events.CreateMessage.Response(message=domain.Message.serialize(message)),
                error=None,
            ).model_dump(mode="json", by_alias=True),
            topic=Topic.chat_message_create.event,
        )
