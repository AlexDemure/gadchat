from src.entrypoints.http.common.helpers.usecases import UsecaseRunner
from src.entrypoints.servers.uploader.application.usecases.files.document import Container
from src.entrypoints.servers.uploader.application.usecases.files.document import Repository
from src.entrypoints.servers.uploader.application.usecases.files.document import Storage
from src.entrypoints.servers.uploader.application.usecases.files.document import Usecase


def dependency() -> UsecaseRunner:
    return UsecaseRunner(
        usecase=lambda session: Usecase(container=Container(repository=Repository(session), storage=Storage())),
        transaction=True,
    )
