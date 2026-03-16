from fastapi import Depends

from src.application.usecases.chats.search import Container
from src.application.usecases.chats.search import Repository
from src.application.usecases.chats.search import Usecase
from src.entrypoints.http.common.deps import read
from src.infrastructure.databases.orm.sqlalchemy.session import Session


def dependency(session: Session = Depends(read)) -> Usecase:
    return Usecase(container=Container(repository=Repository(session)))
