import asyncio
import contextlib

from src.entrypoints.workers.dispatcher.application.usecases.dispatch import dispatch
from src.infrastructure.brokers.kafka import kafka
from src.infrastructure.databases.postgres import postgres
from src.infrastructure.monitoring.logging import logger
from src.infrastructure.monitoring.sentry import sentry
from src.infrastructure.storages.redis import redis


@contextlib.asynccontextmanager
async def lifespan():
    sentry.start()
    postgres.start()
    await redis.start()
    await kafka.start()
    logger.info("Dispatcher application started")
    yield
    logger.info("Dispatcher application shutdown")
    await kafka.close()
    await redis.shutdown()
    postgres.shutdown()
    sentry.shutdown()


async def main() -> None:
    async with lifespan():
        while True:
            await dispatch()
            await asyncio.sleep(0.5)
