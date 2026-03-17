from src.entrypoints.servers.chat.application.usecases.chats.search import Container
from src.entrypoints.servers.chat.application.usecases.chats.search import Repository
from src.entrypoints.servers.chat.application.usecases.chats.search import Usecase
from src.helpers import UsecaseRunner


def dependency():
    return UsecaseRunner(
        usecase=lambda session: Usecase(container=Container(repository=Repository(session))),
        transaction=False,
    )
