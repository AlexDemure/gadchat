import uuid

from fastapi import HTTPException

from src.application.utils.chats.message import compute_shard_key
from src.common.formats.utils import date
from src.infrastructure.databases.orm.sqlalchemy import queries
from src.infrastructure.databases.orm.sqlalchemy.session import Session
from src.infrastructure.databases.postgres.crud import Chat
from src.infrastructure.databases.postgres.crud import Member


class Repositories:
    def __init__(self, session: Session) -> None:
        self.chat = Chat
        self.member = Member
        self.session = session


class Security:
    def __init__(self) -> None: ...


class Container:
    def __init__(self, repositories: Repositories, security: Security) -> None:
        self.repositories = repositories
        self.security = security


class Usecase:
    def __init__(self, container: Container) -> None:
        self.container = container

    async def __call__(self, user_id: str, members: list[str]) -> dict[str, object]:
        session = self.container.repositories.session

        normalized_members = sorted({member for member in members if member and member != user_id})
        if not normalized_members:
            raise HTTPException(status_code=400, detail="members must include at least one other user")

        if len(normalized_members) == 1:
            chat = await self.container.repositories.chat.direct(session, user_id, normalized_members[0])
            if chat:
                return {
                    "chat": chat,
                    "members": await self.container.repositories.member.ids(
                        session,
                        queries.Filter.eq(key="chat_id", value=chat.id),
                        queries.Filter.eq(key="shard_id", value=chat.shard_id),
                    ),
                    "last_message": None,
                }

        all_members = sorted([user_id, *normalized_members])
        chat = await self.container.repositories.chat.create(
            session,
            {
                "id": uuid.uuid4(),
                "kind": "direct" if len(normalized_members) == 1 else "group",
                "title": None,
                "shard_id": compute_shard_key(":".join(all_members)),
                "created": date.now(),
            },
        )

        for member in all_members:
            await self.container.repositories.member.create(
                session,
                {
                    "id": uuid.uuid4(),
                    "shard_id": chat.shard_id,
                    "chat_id": chat.id,
                    "user_id": member,
                    "created": date.now(),
                },
            )

        return {
            "chat": chat,
            "members": all_members,
            "last_message": None,
        }
