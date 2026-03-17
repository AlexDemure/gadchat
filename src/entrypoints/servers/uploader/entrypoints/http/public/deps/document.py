from src.entrypoints.http.common.helpers.usecases import UsecaseRunner
from src.entrypoints.servers.uploader.application.usecases import DocumentContainer
from src.entrypoints.servers.uploader.application.usecases import DocumentRepository
from src.entrypoints.servers.uploader.application.usecases import DocumentStorage
from src.entrypoints.servers.uploader.application.usecases import UploadDocument


def dependency() -> UsecaseRunner:
    return UsecaseRunner(
        usecase=lambda session: UploadDocument(
            container=DocumentContainer(repository=DocumentRepository(session), storage=DocumentStorage())
        ),
        transaction=True,
    )
