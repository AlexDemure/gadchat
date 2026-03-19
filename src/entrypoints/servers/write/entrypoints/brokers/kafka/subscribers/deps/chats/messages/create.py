from src.entrypoints.servers.write.application.usecases.chats.messages.create import Usecase


def dependency() -> Usecase:
    return Usecase()
