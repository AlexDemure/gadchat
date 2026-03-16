from src.application.utils.chats.message import parse_ingest_event
from src.infrastructure.databases.orm.sqlalchemy.session import Session

from . import create


class Repository:
    def __init__(self, session: Session) -> None:
        self.session = session


class Security:
    def __init__(self) -> None: ...


class Container:
    def __init__(self, repository: Repository, security: Security) -> None:
        self.repository = repository
        self.security = security


class Usecase:
    def __init__(self, container: Container) -> None:
        self.container = container

    async def __call__(self, event: dict[str, object]) -> dict[str, object]:
        payload = parse_ingest_event(event)

        usecase = create.Usecase(
            create.Container(
                repository=create.Repository(self.container.repository.session),
                security=create.Security(),
            )
        )
        return await usecase(
            sender_id=payload["sender_id"],
            body=payload["body"],
            attachments=payload["attachments"],
            chat_id=payload["chat_id"],
            peer_user_id=payload["peer_user_id"],
        )
