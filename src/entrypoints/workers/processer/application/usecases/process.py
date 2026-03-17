import logging
import typing

from faststream.kafka.annotations import KafkaMessage

from src.configuration import settings
from src.infrastructure.brokers.kafka import kafka


logger = logging.getLogger("gadchat.worker")


async def process_event(event: dict[str, typing.Any]) -> None: ...


@kafka.subscriber(settings.KAFKA_TOPIC_OPERATIONS, group_id=settings.KAFKA_GROUP_ID)
async def command(event: dict[str, typing.Any], _message: KafkaMessage) -> None:
    await process_event(event)
