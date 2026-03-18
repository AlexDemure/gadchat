from src.entrypoints.servers.uploader.application.usecases.files.video import Usecase


def dependency() -> Usecase:
    return Usecase()
