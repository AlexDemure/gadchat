import contextlib
import typing

from fastapi import FastAPI
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from uvicorn import Config
from uvicorn import Server

from src.common.http.collections import HTTPError
from src.entrypoints.servers.core.entrypoints import http
from src.framework.openapi import OpenAPI
from src.infrastructure.databases.postgres import postgres
from src.infrastructure.monitoring.health import health
from src.infrastructure.monitoring.logging import logger
from src.infrastructure.monitoring.sentry import sentry
from src.infrastructure.storages.minio import minio


@contextlib.asynccontextmanager
async def lifespan(_app: FastAPI) -> typing.Any:
    sentry.start()
    postgres.start()
    minio.start()
    logger.info("Core application started")
    yield
    logger.info("Core application shutdown")
    minio.shutdown()
    postgres.shutdown()
    sentry.shutdown()


app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None)


@app.get("/api/swagger", include_in_schema=False, response_class=HTMLResponse)
def swagger() -> HTMLResponse:
    return get_swagger_ui_html(openapi_url="/api/specification.json", title=app.title)


@app.get("/api/redoc", include_in_schema=False, response_class=HTMLResponse)
def redoc() -> HTMLResponse:
    return get_redoc_html(openapi_url="/api/specification.json", title=app.title)


@app.get("/api/specification.json", include_in_schema=False, response_model=dict)
def specification() -> dict[typing.Any, typing.Any]:
    return OpenAPI(app).generate()


@app.exception_handler(HTTPError)
async def error_handler(_: Request, error: HTTPError) -> JSONResponse:
    return JSONResponse(status_code=error.code, content=error.http)


app.mount("/api/static", StaticFiles(directory="src/static"), name="static")

app.include_router(health.router)

app.include_router(http.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def main(port: int) -> None:
    await Server(Config(app=app, host="0.0.0.0", port=port, reload=False)).serve()
