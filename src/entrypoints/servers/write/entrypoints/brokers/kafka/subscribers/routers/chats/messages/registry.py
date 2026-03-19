from faststream.kafka import KafkaRouter

from .create import router as create_router


router = KafkaRouter()

router.include_router(create_router)
