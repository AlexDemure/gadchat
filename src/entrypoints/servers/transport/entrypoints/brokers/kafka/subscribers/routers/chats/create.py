from fastapi import Depends
from faststream.kafka import KafkaRouter

from src.application.protocols import events
from src.entrypoints.servers.transport.application.usecases.events.chats.create import Usecase
from src.entrypoints.servers.transport.entrypoints.brokers.kafka.subscribers.deps.chats.create import dependency
from src.infrastructure.brokers.collections import Group
from src.infrastructure.brokers.collections import Topic


router = KafkaRouter()


@router.subscriber(Topic.chat_create.event, group_id=Group.event)
async def event(
    payload: events.CreateChat,
    usecase: Usecase = Depends(dependency),
) -> None:
    await usecase.execute(payload)
