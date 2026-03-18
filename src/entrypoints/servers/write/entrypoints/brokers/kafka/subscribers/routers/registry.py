from faststream.kafka import KafkaRouter

from . import chats


router = KafkaRouter()

router.include_router(chats.router)
