from src.entrypoints.servers.write.application.usecases.chats.create import Usecase


def dependency() -> Usecase:
    return Usecase()
