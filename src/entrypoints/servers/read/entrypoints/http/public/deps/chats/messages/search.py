from src.entrypoints.servers.read.application.usecases.chats.messages.search import Usecase


def dependency() -> Usecase:
    return Usecase()
