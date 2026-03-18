from src.entrypoints.servers.write.application.usecases.chats.process import Usecase

def dependency() -> Usecase:
    return Usecase()
