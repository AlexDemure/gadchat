from src.entrypoints.http.common.helpers.usecases import UsecaseRunner
from src.entrypoints.servers.uploader.application.usecases.files.video import Container
from src.entrypoints.servers.uploader.application.usecases.files.video import Repository
from src.entrypoints.servers.uploader.application.usecases.files.video import Storage
from src.entrypoints.servers.uploader.application.usecases.files.video import Usecase


def dependency() -> UsecaseRunner:
    return UsecaseRunner(
        usecase=lambda session: Usecase(container=Container(repository=Repository(session), storage=Storage())),
        transaction=True,
    )
