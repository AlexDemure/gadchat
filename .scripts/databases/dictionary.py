import asyncio
import json

from src.common.formats.utils import string
from src.configuration import settings
from src.domain.collections import RoleNotFound
from src.infrastructure.databases.orm.sqlalchemy import SQLAlchemy
from src.infrastructure.databases.orm.sqlalchemy.queries import Filter
from src.infrastructure.databases.postgres import adapters


async def upload() -> None:
    dictionaries = {
        "role": {
            "adapter": adapters.repositories.Role,
            "filename": "src/static/databases/roles.json",
            "error": RoleNotFound,
        }
    }

    async with SQLAlchemy(url=settings.asyncpg).write() as _session:
        for _, value in dictionaries.items():
            adapter = value["adapter"](_session)  # type:ignore

            with open(value["filename"], "r") as file:
                objects = json.loads(file.read())

            for obj in objects:
                try:
                    await adapter.one(Filter.eq("id", string.lower(obj["id"])))
                except value["error"]:
                    await adapter.create(
                        {
                            "id": string.lower(obj["id"]),
                            "name": string.lower(obj["name"]),
                        }
                    )


if __name__ == "__main__":
    asyncio.run(upload())
