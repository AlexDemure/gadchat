from fastapi import Depends
from faststream.kafka import KafkaRouter

from src.application.protocols import commands
from src.entrypoints.servers.write.application.usecases.chats.create import Usecase
from src.entrypoints.servers.write.entrypoints.brokers.kafka.subscribers.deps.chats.create import dependency
from src.infrastructure.brokers.collections import Group
from src.infrastructure.brokers.collections import Topic


router = KafkaRouter()


@router.subscriber(Topic.chat_create.command, group_id=Group.command)
async def create(
    command: commands.CreateChat,
    usecase: Usecase = Depends(dependency),
) -> None:
    await usecase.execute(command)
