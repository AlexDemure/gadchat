from src.entrypoints.servers.transport.application.usecases.events.chats.messages.create import Usecase


def dependency() -> Usecase:
    return Usecase()
