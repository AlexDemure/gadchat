from src.application.usecases.users.auth import Container
from src.application.usecases.users.auth import Repository
from src.application.usecases.users.auth import Security
from src.application.usecases.users.auth import Usecase
from src.entrypoints.http.common.helpers.usecases import UsecaseRunner


def dependency():
    return UsecaseRunner(
        usecase=lambda session: Usecase(container=Container(repository=Repository(session), security=Security())),
        transaction=True,
    )
