import asyncio
import logging
import typing

from faststream.kafka.annotations import KafkaMessage

from src.application.usecases.chats.messages import create
from src.configuration import settings
from src.infrastructure.databases.orm.sqlalchemy.queries import Filter
from src.infrastructure.brokers.kafka import kafka
from src.infrastructure.databases.postgres import postgres
from src.infrastructure.databases.postgres import adapters


logger = logging.getLogger("gadchat.worker")


async def process_event(event: dict[str, typing.Any]) -> None:
    async with postgres.orm.write() as session:
        usecase = create.Usecase(
            create.Container(
                repository=create.Repository(session),
            )
        )
        try:
            sender_id = event.get("sender_id")
            chat_id = event.get("chat_id")
            if not isinstance(sender_id, str) or not isinstance(chat_id, str):
                logger.warning("Skip event due to invalid payload: sender_id/chat_id required")
                return

            user = await adapters.repositories.User(session).one(Filter.eq(key="external_id", value=sender_id))
            await usecase(
                user=user,
                chat_id=chat_id,
                text=event.get("text") if isinstance(event.get("text"), str) else None,
                reply=reply
                if isinstance((reply := event.get("reply")), dict)
                and isinstance(reply.get("message_id"), str)
                else None,
                forward=forward
                if isinstance((forward := event.get("forward")), dict)
                and isinstance(forward.get("chat_id"), str)
                and isinstance(forward.get("message_id"), str)
                else None,
                file_ids=[item for item in file_ids if isinstance(item, str)]
                if isinstance((file_ids := event.get("file_ids")), list)
                else [],
            )
        except Exception as exc:
            logger.warning("Skip event due to processing error: %s", exc)
            return


@kafka.subscriber(settings.KAFKA_TOPIC_INGRESS)
async def command(event: dict[str, typing.Any], _message: KafkaMessage) -> None:
    await process_event(event)


async def main() -> None:
    try:
        postgres.start()
        await kafka.start()
        await asyncio.Future()
    finally:
        await kafka.close()
        await postgres.orm.engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
