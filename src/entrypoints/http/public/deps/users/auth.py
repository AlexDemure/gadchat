from src.application.usecases.users.auth import Container
from src.application.usecases.users.auth import Repositories
from src.application.usecases.users.auth import Security
from src.application.usecases.users.auth import Usecase


def dependency() -> Usecase:
    return Usecase(container=Container(repositories=Repositories(), security=Security()))
