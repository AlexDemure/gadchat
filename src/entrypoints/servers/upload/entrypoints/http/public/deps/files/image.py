from src.entrypoints.servers.upload.application.usecases.files.image import Usecase


def dependency() -> Usecase:
    return Usecase()
