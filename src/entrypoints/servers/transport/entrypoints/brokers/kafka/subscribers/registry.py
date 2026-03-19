from faststream.kafka import KafkaRouter

from .routers import router as subscribers_router


router = KafkaRouter()

router.include_router(subscribers_router)
