from src.application.usecases.users.jwt import Container
from src.application.usecases.users.jwt import Repository
from src.application.usecases.users.jwt import Security
from src.application.usecases.users.jwt import Usecase
from src.entrypoints.http.common.helpers.usecases import UsecaseRunner


def dependency():
    return UsecaseRunner(
        usecase=lambda session: Usecase(container=Container(repository=Repository(session), security=Security())),
        transaction=False,
    )
