import uuid

from fastapi import HTTPException

from src.application.utils.chats.message import compute_shard_key
from src.common.formats.utils import date
from src.infrastructure.databases.orm.sqlalchemy.session import Session
from src.infrastructure.databases.postgres import adapters


class Repository:
    def __init__(self, session: Session) -> None:
        self.chat = adapters.repositories.Chat(session)
        self.chat_member = adapters.repositories.ChatMember(session)
        self.member = adapters.repositories.Member(session)


class Security:
    def __init__(self) -> None: ...


class Container:
    def __init__(self, repository: Repository, security: Security) -> None:
        self.repository = repository
        self.security = security


class Usecase:
    def __init__(self, container: Container) -> None:
        self.container = container

    async def __call__(self, user_id: str, members: list[str]) -> dict[str, object]:
        normalized_members = sorted({member for member in members if member and member != user_id})
        if not normalized_members:
            raise HTTPException(status_code=400, detail="members must include at least one other user")

        if len(normalized_members) == 1:
            chat = await self.container.repository.chat.direct(user_id, normalized_members[0])
            if chat:
                return {
                    "chat": chat,
                    "members": await self.container.repository.chat_member.users(chat.id, chat.shard_id),
                    "last_message": None,
                }

        all_members = sorted([user_id, *normalized_members])
        created = date.now()
        chat = await self.container.repository.chat.create(
            {
                "id": uuid.uuid4(),
                "kind": "direct" if len(normalized_members) == 1 else "group",
                "title": None,
                "options": {},
                "shard_id": compute_shard_key(":".join(all_members)),
                "created": created,
            },
        )

        for member_user_id in all_members:
            member = await self.container.repository.member.ensure(user_id=member_user_id, created=created)
            await self.container.repository.chat_member.create(
                {
                    "id": uuid.uuid4(),
                    "shard_id": chat.shard_id,
                    "chat_id": chat.id,
                    "member_id": member.id,
                    "created": created,
                },
            )

        return {
            "chat": chat,
            "members": await self.container.repository.chat_member.users(chat.id, chat.shard_id),
            "last_message": None,
        }
