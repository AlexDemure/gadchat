from src.entrypoints.servers.uploader.application.usecases.files.audio import Usecase


def dependency() -> Usecase:
    return Usecase()
