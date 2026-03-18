from src.entrypoints.servers.upload.application.usecases.files.document import Usecase


def dependency() -> Usecase:
    return Usecase()
