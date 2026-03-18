from src.entrypoints.servers.upload.application.usecases.files.audio import Usecase


def dependency() -> Usecase:
    return Usecase()
