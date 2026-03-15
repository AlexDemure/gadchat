import asyncio
import contextlib
import typing

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from uvicorn import Config
from uvicorn import Server

from src.entrypoints import http
from src.entrypoints import websockets
from src.entrypoints.workers import workers
from src.framework.background import background
from src.infrastructure.brokers.kafka import kafka
from src.infrastructure.databases.postgres import postgres
from src.infrastructure.storages.minio import minio
from src.infrastructure.storages.redis import redis


@contextlib.asynccontextmanager
async def lifespan(_app: FastAPI) -> typing.Any:
    postgres.start()
    minio.start()
    await redis.start()
    workers()
    background.start()
    await kafka.start()
    yield
    background.shutdown()
    await kafka.close()
    await redis.shutdown()
    minio.shutdown()
    postgres.shutdown()


app = FastAPI(title="gadchat-mvp", version="0.1.0", lifespan=lifespan)

app.mount("/api/static", StaticFiles(directory="src/static"), name="static")

app.include_router(http.router)

app.include_router(websockets.router)


async def run() -> None:
    await Server(
        Config(
            app="src.bootstrap.server:app",
            host="0.0.0.0",
            port=8000,
            reload=False,
        )
    ).serve()


if __name__ == "__main__":
    asyncio.run(run())
