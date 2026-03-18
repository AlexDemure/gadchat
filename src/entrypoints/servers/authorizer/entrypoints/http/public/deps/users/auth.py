from src.entrypoints.servers.authorizer.application.usecases.users.auth import Usecase


def dependency() -> Usecase:
    return Usecase()
