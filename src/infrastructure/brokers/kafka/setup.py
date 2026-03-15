from faststream.kafka import KafkaBroker

from src.configuration import settings


kafka = KafkaBroker(settings.KAFKA_HOST)
