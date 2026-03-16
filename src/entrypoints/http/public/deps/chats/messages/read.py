from src.application.usecases.chats.messages.read import Container
from src.application.usecases.chats.messages.read import Repository
from src.application.usecases.chats.messages.read import Usecase
from src.entrypoints.http.common.uow.session import writable
from src.infrastructure.databases.orm.sqlalchemy.session import Session


def factory(session: Session) -> Usecase:
    return Usecase(container=Container(repository=Repository(session)))


def dependency():
    return writable(factory=factory)
