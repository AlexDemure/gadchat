import uuid

from fastapi import HTTPException

from src.common.formats.utils import date
from src.infrastructure.databases.orm.sqlalchemy.session import Session
from src.infrastructure.databases.postgres import adapters


class Repository:
    def __init__(self, session: Session) -> None:
        self.chat = adapters.repositories.Chat(session)
        self.member = adapters.repositories.Member(session)
        self.role = adapters.repositories.Role(session)
        self.user = adapters.repositories.User(session)


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
                    "members": await self.container.repository.member.users(chat.id),
                    "last_message": None,
                }

        all_members = sorted([user_id, *normalized_members])
        created = date.now()
        admin_role = await self.container.repository.role.ensure(name="admin")
        user_role = await self.container.repository.role.ensure(name="user")
        chat = await self.container.repository.chat.create(
            {
                "id": str(uuid.uuid4()),
                "title": None,
                "options": {},
                "created": created,
            },
        )

        for member_user_id in all_members:
            user = await self.container.repository.user.ensure(external_id=member_user_id)
            await self.container.repository.member.create(
                {
                    "id": str(uuid.uuid4()),
                    "chat_id": chat.id,
                    "user_id": user.id,
                    "role_id": admin_role.id
                    if len(normalized_members) > 1 and member_user_id == user_id
                    else user_role.id,
                    "position": None,
                    "notifications": 0,
                },
            )

        return {
            "chat": chat,
            "members": await self.container.repository.member.users(chat.id),
            "last_message": None,
        }
