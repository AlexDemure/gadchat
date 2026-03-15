import typing

from sqlalchemy import and_
from sqlalchemy import desc
from sqlalchemy import func
from sqlalchemy import select

from src.infrastructure.databases.orm.sqlalchemy import queries
from src.infrastructure.databases.orm.sqlalchemy.session import Session
from src.infrastructure.databases.postgres.crud import Member
from src.infrastructure.databases.postgres.tables import Chat
from src.infrastructure.databases.postgres.tables import Message


class Repositories:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.member = Member


class Security:
    def __init__(self) -> None: ...


class Container:
    def __init__(self, repositories: Repositories, security: Security) -> None:
        self.repositories = repositories
        self.security = security


class Usecase:
    def __init__(self, container: Container) -> None:
        self.container = container

    async def __call__(self, user_id: str, limit: int = 20) -> dict[str, typing.Any]:
        session = self.container.repositories.session

        latest_subquery = (
            select(
                Message.chat_id,
                func.max(Message.created).label("latest_created"),
            )
            .group_by(Message.chat_id)
            .subquery()
        )

        rows = await session.execute(
            select(
                Chat.id,
                Chat.kind,
                Chat.title,
                latest_subquery.c.latest_created,
                Message.body,
            )
            .join(self.container.repositories.member.table, self.container.repositories.member.table.chat_id == Chat.id)
            .outerjoin(latest_subquery, latest_subquery.c.chat_id == Chat.id)
            .outerjoin(
                Message,
                and_(
                    Message.chat_id == Chat.id,
                    Message.created == latest_subquery.c.latest_created,
                ),
            )
            .where(self.container.repositories.member.table.user_id == user_id)
            .order_by(desc(latest_subquery.c.latest_created).nullslast(), desc(Chat.created))
            .limit(limit)
        )

        items = []
        for chat_id, _kind, _title, _latest_created, _body in rows.all():
            chat = await session.get(Chat, chat_id)
            if chat is None:
                continue
            last_message_row = await session.execute(
                select(Message)
                .where(Message.chat_id == chat_id)
                .order_by(desc(Message.created), desc(Message.id))
                .limit(1)
            )
            last_message = last_message_row.scalar_one_or_none()
            members = await self.container.repositories.member.ids(
                session,
                queries.Filter.eq(key="chat_id", value=chat_id),
            )
            items.append(
                {
                    "chat": chat,
                    "last_message": last_message,
                    "members": members,
                }
            )

        return {"items": items}
