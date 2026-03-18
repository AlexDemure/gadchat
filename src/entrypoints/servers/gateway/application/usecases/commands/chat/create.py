import typing

from src.application.protocols.commands.chat import CreateChat
from src.application.protocols.transport import Event
from src.infrastructure.brokers.collections import EventStatus
from src.infrastructure.brokers.collections import Topic
from src.infrastructure.brokers.kafka import kafka
from src.infrastructure.security.jwt import jwt


class Security:
    def __init__(self) -> None:
        self.jwt = jwt


class Broker:
    def __init__(self) -> None:
        self.kafka = kafka


class Container:
    def __init__(self, security: Security, broker: Broker) -> None:
        self.security = security
        self.broker = broker


class Usecase:
    def __init__(self) -> None:
        self.container = None

    def build(self) -> None:
        self.container = Container(security=Security(), broker=Broker())

    async def execute(self, token: str, payload: dict[str, typing.Any]) -> Event:
        self.build()

        user_id = self.container.security.jwt.decode(token=token).sub

        command = CreateChat.model_validate(payload)

        command.payload.user_ids.append(user_id)

        await self.container.broker.kafka.publish(command.model_dump(mode="json"), topic=Topic.chat_create.command)

        command.status = EventStatus.accepted

        return command
