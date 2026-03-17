from src.entrypoints.servers.uploader.application.usecases.files.document import Container
from src.entrypoints.servers.uploader.application.usecases.files.document import Repository
from src.entrypoints.servers.uploader.application.usecases.files.document import Storage
from src.entrypoints.servers.uploader.application.usecases.files.document import Usecase
from src.helpers.usecases import UsecaseRunner


def dependency() -> UsecaseRunner:
    return UsecaseRunner(
        usecase=lambda session: Usecase(container=Container(repository=Repository(session), storage=Storage())),
        transaction=True,
    )
