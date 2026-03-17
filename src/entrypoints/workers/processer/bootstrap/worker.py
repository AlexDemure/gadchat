import asyncio

from src.infrastructure.brokers.kafka import kafka
from src.infrastructure.databases.postgres import postgres

from ..application.usecases.process import command


async def main() -> None:
    try:
        postgres.start()
        await kafka.start()
        _ = command
        await asyncio.Future()
    finally:
        await kafka.close()
        await postgres.orm.engine.dispose()
