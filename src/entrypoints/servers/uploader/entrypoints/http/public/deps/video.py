from src.entrypoints.http.common.helpers.usecases import UsecaseRunner
from src.entrypoints.servers.uploader.application.usecases import UploadVideo
from src.entrypoints.servers.uploader.application.usecases import VideoContainer
from src.entrypoints.servers.uploader.application.usecases import VideoRepository
from src.entrypoints.servers.uploader.application.usecases import VideoStorage


def dependency() -> UsecaseRunner:
    return UsecaseRunner(
        usecase=lambda session: UploadVideo(
            container=VideoContainer(repository=VideoRepository(session), storage=VideoStorage())
        ),
        transaction=True,
    )
