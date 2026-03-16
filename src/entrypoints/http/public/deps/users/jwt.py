from src.application.usecases.users.jwt import Container
from src.application.usecases.users.jwt import Repository
from src.application.usecases.users.jwt import Security
from src.application.usecases.users.jwt import Usecase
from src.entrypoints.http.common.uow.session import readable
from src.infrastructure.databases.orm.sqlalchemy.session import Session


def factory(session: Session) -> Usecase:
    return Usecase(container=Container(repository=Repository(session), security=Security()))


def dependency():
    return readable(factory=factory)
