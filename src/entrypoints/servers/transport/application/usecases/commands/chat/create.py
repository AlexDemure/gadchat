from src.application.protocols.commands.chat import CreateChat
from src.application.protocols.transport import Event
from src.infrastructure.brokers.collections import EventStatus
from src.infrastructure.brokers.collections import Topic
from src.infrastructure.brokers.kafka import kafka


class Broker:
    def __init__(self) -> None:
        self.kafka = kafka


class Container:
    def __init__(self, broker: Broker) -> None:
        self.broker = broker


class Usecase:
    def __init__(self) -> None:
        self.container = None

    def build(self) -> None:
        self.container = Container(broker=Broker())

    async def execute(self, command: CreateChat) -> Event:
        self.build()

        await self.container.broker.kafka.publish(command.model_dump(mode="json"), topic=Topic.chat_create.command)

        command.status = EventStatus.accepted

        return command
