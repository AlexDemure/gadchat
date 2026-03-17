from src.application.usecases.chats.position import Container
from src.application.usecases.chats.position import Repository
from src.application.usecases.chats.position import Usecase
from src.entrypoints.http.common.helpers.usecases import UsecaseRunner


def dependency():
    return UsecaseRunner(
        usecase=lambda session: Usecase(container=Container(repository=Repository(session))),
        transaction=True,
    )
