import asyncio
import contextlib
import typing

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from uvicorn import Config
from uvicorn import Server

from src.entrypoints import http
from src.entrypoints import websockets
from src.entrypoints.cron import jobs
from src.entrypoints.workers import workers
from src.framework.background import background
from src.framework.openapi import OpenAPI
from src.infrastructure.brokers.kafka import kafka
from src.infrastructure.databases.postgres import postgres
from src.infrastructure.monitoring.asyncio.detector import detector
from src.infrastructure.monitoring.health import health
from src.infrastructure.monitoring.logging import logger
from src.infrastructure.monitoring.sentry import sentry
from src.infrastructure.scheduling.apscheduler import apscheduler
from src.infrastructure.storages.minio import minio
from src.infrastructure.storages.redis import redis


@contextlib.asynccontextmanager
async def lifespan(_app: FastAPI) -> typing.Any:
    sentry.start()
    postgres.start()
    minio.start()
    await redis.start()
    workers()
    background.start()
    apscheduler.start()
    jobs()
    await kafka.start()
    detector.start()
    logger.info("Application started")
    yield
    logger.info("Application shutdown")
    detector.shutdown()
    background.shutdown()
    apscheduler.shutdown()
    await kafka.close()
    await redis.shutdown()
    minio.shutdown()
    postgres.shutdown()
    sentry.shutdown()


app = FastAPI(
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
)


@app.get(
    "/api/swagger",
    description="Swagger Documentation",
    include_in_schema=False,
    response_class=HTMLResponse,
)
def swagger() -> HTMLResponse:
    return get_swagger_ui_html(openapi_url="/api/specification.json", title=app.title)


@app.get(
    "/api/redoc",
    description="Redoc Documentation",
    include_in_schema=False,
    response_class=HTMLResponse,
)
def redoc() -> HTMLResponse:
    return get_redoc_html(openapi_url="/api/specification.json", title=app.title)


@app.get(
    "/api/specification.json",
    description="API Specification",
    include_in_schema=False,
    response_model=dict,
)
def specification() -> dict[typing.Any, typing.Any]:
    return OpenAPI(app).generate()


app.mount("/api/static", StaticFiles(directory="src/static"), name="static")

app.include_router(redis.router)

app.include_router(health.router)

app.include_router(http.router)

app.include_router(websockets.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def run() -> None:
    await Server(
        Config(
            app=app,
            host="0.0.0.0",
            port=8000,
            reload=False,
        )
    ).serve()


if __name__ == "__main__":
    asyncio.run(run())
