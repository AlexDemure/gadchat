from faststream.kafka import KafkaRouter

from . import create
from . import messages


router = KafkaRouter()

router.include_router(create.router)
router.include_router(messages.router)
