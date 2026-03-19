from src.entrypoints.servers.auth.application.usecases.users.current import Usecase


def dependency() -> Usecase:
    return Usecase()
