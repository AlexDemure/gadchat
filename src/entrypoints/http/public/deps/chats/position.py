from src.application.usecases.chats.position import Container
from src.application.usecases.chats.position import Repository
from src.application.usecases.chats.position import Usecase
from src.entrypoints.http.common.uow.session import writable
from src.infrastructure.databases.orm.sqlalchemy.session import Session


def factory(session: Session) -> Usecase:
    return Usecase(container=Container(repository=Repository(session)))


def dependency():
    return writable(factory=factory)
