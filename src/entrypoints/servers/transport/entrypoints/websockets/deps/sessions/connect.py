from src.entrypoints.servers.transport.application.usecases.sessions.connect import Usecase


def dependency() -> Usecase:
    return Usecase()
