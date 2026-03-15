import asyncio
import typing

from faststream.kafka.annotations import KafkaMessage

from src.application.usecases.chats.messages import ingest
from src.configuration import settings
from src.entrypoints.http.common.collections import REDIS_CHANNEL_EVENTS
from src.entrypoints.http.public.schemas.chat import MessageCreated
from src.infrastructure.brokers.kafka import kafka
from src.infrastructure.databases.postgres import postgres
from src.infrastructure.storages.redis import redis


async def process_event(event: dict[str, typing.Any]) -> None:
    async with postgres.orm.write() as session:
        usecase = ingest.Usecase(
            ingest.Container(
                repositories=ingest.Repositories(session),
                security=ingest.Security(),
            )
        )
        stored = await usecase(event)
        delivery_event = MessageCreated.serialize(
            chat_id=str(stored["chat"].id),
            message=stored["message"],
            recipients=stored["recipients"],
        )
        await redis.publish(REDIS_CHANNEL_EVENTS, delivery_event)


@kafka.subscriber(settings.KAFKA_TOPIC_INGRESS)
async def command(event: dict[str, typing.Any], _message: KafkaMessage) -> None:
    await process_event(event)


async def main() -> None:
    try:
        postgres.start()
        await redis.start()
        await kafka.start()
        await asyncio.Future()
    finally:
        await kafka.close()
        await redis.shutdown()
        await postgres.orm.engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
