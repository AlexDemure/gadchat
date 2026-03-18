from src.common.formats.utils import date
from src.decorators import sessionmaker
from src.domain.collections import MessageNotFound
from src.domain.collections import UserNotChatMember
from src.infrastructure.databases.orm.sqlalchemy.queries import And
from src.infrastructure.databases.orm.sqlalchemy.queries import Filter
from src.infrastructure.databases.orm.sqlalchemy.session import Session
from src.infrastructure.databases.postgres import adapters
from src.infrastructure.databases.postgres.tables import User


class Repository:
    def __init__(self, session: Session) -> None:
        self.member = adapters.repositories.Member(session)
        self.message = adapters.repositories.Message(session)


class Container:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository


class Usecase:
    def __init__(self) -> None:
        self.container = None

    def build(self, session: Session) -> None:
        self.container = Container(repository=Repository(session))

    async def validate(self, chat_id: str, message_id: str, user_id: str) -> None:
        if not await self.container.repository.member.exists(
            And.combine(
                Filter.eq(key="chat_id", value=chat_id),
                Filter.eq(key="user_id", value=user_id),
            )
        ):
            raise UserNotChatMember

        if not await self.container.repository.message.exists(
            And.combine(
                Filter.eq(key="id", value=message_id),
                Filter.eq(key="chat_id", value=chat_id),
            )
        ):
            raise MessageNotFound

    @sessionmaker.write
    async def execute(self, session: Session, user: User, chat_id: str, message_id: str) -> None:
        self.build(session)
        await self.validate(chat_id=chat_id, message_id=message_id, user_id=user.id)
        await self.container.repository.message.update(id=message_id, pinned=date.now())
