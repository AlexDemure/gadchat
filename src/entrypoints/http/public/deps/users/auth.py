from src.application.usecases.users.auth import Container
from src.application.usecases.users.auth import Repository
from src.application.usecases.users.auth import Security
from src.application.usecases.users.auth import Usecase
from src.entrypoints.http.common.uow.session import writable
from src.infrastructure.databases.orm.sqlalchemy.session import Session


def factory(session: Session) -> Usecase:
    return Usecase(container=Container(repository=Repository(session), security=Security()))


def dependency():
    return writable(factory=factory)
