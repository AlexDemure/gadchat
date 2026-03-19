from src.entrypoints.servers.transport.application.usecases.events.chats.create import Usecase


def dependency() -> Usecase:
    return Usecase()
