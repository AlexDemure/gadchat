from src.entrypoints.servers.uploader.application.usecases.files.document import Usecase


def dependency() -> Usecase:
    return Usecase()
