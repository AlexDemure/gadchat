from src.entrypoints.servers.auth.application.usecases.users.login import Usecase


def dependency() -> Usecase:
    return Usecase()
