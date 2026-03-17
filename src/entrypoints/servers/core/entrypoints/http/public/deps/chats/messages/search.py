from src.entrypoints.http.common.helpers.usecases import UsecaseRunner
from src.entrypoints.servers.core.application.usecases.chats.messages.search import Container
from src.entrypoints.servers.core.application.usecases.chats.messages.search import Repository
from src.entrypoints.servers.core.application.usecases.chats.messages.search import Usecase


def dependency():
    return UsecaseRunner(
        usecase=lambda session: Usecase(container=Container(repository=Repository(session))),
        transaction=False,
    )
