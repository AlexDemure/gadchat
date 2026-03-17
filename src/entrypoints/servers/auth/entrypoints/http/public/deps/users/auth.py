from src.entrypoints.http.common.helpers.usecases import UsecaseRunner
from src.entrypoints.servers.auth.application.usecases.users.auth import Container
from src.entrypoints.servers.auth.application.usecases.users.auth import Repository
from src.entrypoints.servers.auth.application.usecases.users.auth import Security
from src.entrypoints.servers.auth.application.usecases.users.auth import Usecase


def dependency() -> UsecaseRunner:
    return UsecaseRunner(
        usecase=lambda session: Usecase(container=Container(repository=Repository(session), security=Security())),
        transaction=True,
    )
