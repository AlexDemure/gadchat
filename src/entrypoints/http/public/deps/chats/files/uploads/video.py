from src.application.usecases.chats.files.uploads.video import Container
from src.application.usecases.chats.files.uploads.video import Repository
from src.application.usecases.chats.files.uploads.video import Storage
from src.application.usecases.chats.files.uploads.video import Usecase
from src.entrypoints.http.common.helpers.usecases import UsecaseRunner


def dependency():
    return UsecaseRunner(
        usecase=lambda session: Usecase(container=Container(repository=Repository(session), storage=Storage())),
        transaction=True,
    )
