from src.entrypoints.servers.transport.application.usecases.commands.chats.messages.create import Usecase


def dependency() -> Usecase:
    return Usecase()
