from src.application.usecases.chats.messages.search import Container
from src.application.usecases.chats.messages.search import Repository
from src.application.usecases.chats.messages.search import Usecase
from src.entrypoints.http.common.uow.session import readable
from src.infrastructure.databases.orm.sqlalchemy.session import Session


def factory(session: Session) -> Usecase:
    return Usecase(container=Container(repository=Repository(session)))


def dependency():
    return readable(factory=factory)
