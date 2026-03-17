from src.entrypoints.http.common.helpers.usecases import UsecaseRunner
from src.entrypoints.servers.uploader.application.usecases.files.image import Container
from src.entrypoints.servers.uploader.application.usecases.files.image import Repository
from src.entrypoints.servers.uploader.application.usecases.files.image import Storage
from src.entrypoints.servers.uploader.application.usecases.files.image import Usecase


def dependency() -> UsecaseRunner:
    return UsecaseRunner(
        usecase=lambda session: Usecase(container=Container(repository=Repository(session), storage=Storage())),
        transaction=True,
    )
