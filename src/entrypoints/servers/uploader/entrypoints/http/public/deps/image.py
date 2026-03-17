from src.entrypoints.http.common.helpers.usecases import UsecaseRunner
from src.entrypoints.servers.uploader.application.usecases import ImageContainer
from src.entrypoints.servers.uploader.application.usecases import ImageRepository
from src.entrypoints.servers.uploader.application.usecases import ImageStorage
from src.entrypoints.servers.uploader.application.usecases import UploadImage


def dependency() -> UsecaseRunner:
    return UsecaseRunner(
        usecase=lambda session: UploadImage(
            container=ImageContainer(repository=ImageRepository(session), storage=ImageStorage())
        ),
        transaction=True,
    )
