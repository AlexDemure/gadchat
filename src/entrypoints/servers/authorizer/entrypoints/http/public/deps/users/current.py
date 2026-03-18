from src.entrypoints.servers.authorizer.application.usecases.users.current import Usecase


def dependency() -> Usecase:
    return Usecase()
