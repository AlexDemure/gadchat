from src.entrypoints.servers.upload.application.usecases.files.video import Usecase


def dependency() -> Usecase:
    return Usecase()
