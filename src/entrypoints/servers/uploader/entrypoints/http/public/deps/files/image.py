from src.entrypoints.servers.uploader.application.usecases.files.image import Usecase


def dependency() -> Usecase:
    return Usecase()
