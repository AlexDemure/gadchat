from src.application.usecases.chats.files.uploads.document import Container
from src.application.usecases.chats.files.uploads.document import Repository
from src.application.usecases.chats.files.uploads.document import Storage
from src.application.usecases.chats.files.uploads.document import Usecase
from src.entrypoints.http.common.uow.session import writable
from src.infrastructure.databases.orm.sqlalchemy.session import Session


def factory(session: Session) -> Usecase:
    return Usecase(container=Container(repository=Repository(session), storage=Storage()))


def dependency():
    return writable(factory=factory)
