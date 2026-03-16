from fastapi import Depends

from src.application.usecases.chats.unpin import Container
from src.application.usecases.chats.unpin import Repository
from src.application.usecases.chats.unpin import Security
from src.application.usecases.chats.unpin import Usecase
from src.entrypoints.http.common.deps import write
from src.infrastructure.databases.orm.sqlalchemy.session import Session


def dependency(session: Session = Depends(write)) -> Usecase:
    return Usecase(container=Container(repository=Repository(session), security=Security()))
