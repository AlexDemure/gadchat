from src.application.usecases.users.get import Container
from src.application.usecases.users.get import Repository
from src.application.usecases.users.get import Security
from src.application.usecases.users.get import Usecase


def dependency() -> Usecase:
    return Usecase(container=Container(repository=Repository(), security=Security()))
