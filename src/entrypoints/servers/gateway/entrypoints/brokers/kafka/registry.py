from faststream.kafka.fastapi import KafkaRouter

from src.configuration import settings

from . import subscribers


router = KafkaRouter(
    settings.KAFKA_HOST,
    schema_url="/asyncapi",
    include_in_schema=True,
)


router.include_router(subscribers.router, tags=["Subscriber"])
