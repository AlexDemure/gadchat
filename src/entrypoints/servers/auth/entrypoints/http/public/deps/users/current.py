from src.entrypoints.http.common.helpers.usecases import UsecaseRunner
from src.entrypoints.servers.auth.application.usecases.users.current import Container
from src.entrypoints.servers.auth.application.usecases.users.current import Repository
from src.entrypoints.servers.auth.application.usecases.users.current import Security
from src.entrypoints.servers.auth.application.usecases.users.current import Usecase


def dependency() -> UsecaseRunner:
    return UsecaseRunner(
        usecase=lambda session: Usecase(container=Container(repository=Repository(session), security=Security())),
        transaction=True,
    )
