from src.application.usecases.users.get import Container
from src.application.usecases.users.get import Repositories
from src.application.usecases.users.get import Security
from src.application.usecases.users.get import Usecase


def dependency() -> Usecase:
    return Usecase(container=Container(repositories=Repositories(), security=Security()))
