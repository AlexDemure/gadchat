from src.entrypoints.http.common.helpers.usecases import UsecaseRunner
from src.entrypoints.servers.uploader.application.usecases import AudioContainer
from src.entrypoints.servers.uploader.application.usecases import AudioRepository
from src.entrypoints.servers.uploader.application.usecases import AudioStorage
from src.entrypoints.servers.uploader.application.usecases import UploadAudio


def dependency() -> UsecaseRunner:
    return UsecaseRunner(
        usecase=lambda session: UploadAudio(
            container=AudioContainer(repository=AudioRepository(session), storage=AudioStorage())
        ),
        transaction=True,
    )
