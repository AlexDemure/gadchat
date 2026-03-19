from src.entrypoints.servers.read.application.usecases.chats.search import Usecase


def dependency() -> Usecase:
    return Usecase()
