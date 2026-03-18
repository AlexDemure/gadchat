import typing

from faststream.kafka import KafkaRouter

from src.application.protocols.events.chat import CreateChat
from src.entrypoints.servers.transport.application.usecases.events.chat.create import Usecase
from src.infrastructure.brokers.collections import Group
from src.infrastructure.brokers.collections import Topic


router = KafkaRouter()
usecase = Usecase()


@router.subscriber(Topic.chat_create.event, group_id=Group.event)
async def event(payload: CreateChat) -> typing.Any:
    await usecase.execute(payload)
