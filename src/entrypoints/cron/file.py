import datetime
import uuid

from sqlalchemy import select

from src.common.formats.utils import date
from src.infrastructure.databases.orm.sqlalchemy import queries
from src.infrastructure.databases.postgres import postgres
from src.infrastructure.databases.postgres.crud import File
from src.infrastructure.databases.postgres.tables import Attachment
from src.infrastructure.storages.minio import minio


async def command(limit: int = 500) -> None:
    threshold = date.now() - datetime.timedelta(hours=1)

    async with postgres.orm.write() as session:
        rows = await session.execute(
            select(File.table.id, File.table.key)
            .outerjoin(Attachment, Attachment.file_id == File.table.id)
            .where(
                Attachment.file_id.is_(None),
                File.table.created < threshold,
            )
            .limit(limit)
        )

        files: list[tuple[uuid.UUID, str]] = [(row[0], row[1]) for row in rows.all()]
        deleted: list[uuid.UUID] = []

        for file_id, key in files:
            try:
                await minio.delete(key)
            except Exception:
                continue
            deleted.append(file_id)

        if not deleted:
            return

        await File.delete(
            session,
            queries.Filter.in_(key="id", values=deleted),
        )
