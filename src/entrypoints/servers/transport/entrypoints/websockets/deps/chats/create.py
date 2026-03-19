from src.entrypoints.servers.transport.application.usecases.commands.chats.create import Usecase


def dependency() -> Usecase:
    return Usecase()
