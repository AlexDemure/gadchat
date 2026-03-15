from fastapi import Depends

from src.application.usecases.chats.list import Container
from src.application.usecases.chats.list import Repositories
from src.application.usecases.chats.list import Security
from src.application.usecases.chats.list import Usecase
from src.entrypoints.http.common.deps import read
from src.infrastructure.databases.orm.sqlalchemy.session import Session


def dependency(session: Session = Depends(read)) -> Usecase:
    return Usecase(container=Container(repositories=Repositories(session), security=Security()))
