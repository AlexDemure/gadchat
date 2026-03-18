from src.configuration import settings
from src.infrastructure.databases.orm.sqlalchemy import SQLAlchemy


class Postgres:
    def __init__(self) -> None:
        self._orm: SQLAlchemy | None = None

    def start(self) -> None:
        self._orm = SQLAlchemy(url=settings.asyncpg)

    def shutdown(self) -> None: ...

    @property
    def orm(self) -> SQLAlchemy:
        return self._orm
