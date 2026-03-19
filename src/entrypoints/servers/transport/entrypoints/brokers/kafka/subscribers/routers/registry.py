from faststream.kafka import KafkaRouter

from .chats import router as chats_router


router = KafkaRouter()

router.include_router(chats_router)
