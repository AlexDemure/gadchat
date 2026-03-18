from faststream.kafka import KafkaRouter

from . import chat


router = KafkaRouter()


router.include_router(chat.router)
