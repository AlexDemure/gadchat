from faststream.kafka import KafkaRouter

from . import create


router = KafkaRouter()


router.include_router(create.router)
