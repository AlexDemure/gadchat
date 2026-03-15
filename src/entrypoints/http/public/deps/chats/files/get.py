from fastapi import Depends

from src.application.usecases.chats.files.get import Container
from src.application.usecases.chats.files.get import Repositories
from src.application.usecases.chats.files.get import Security
from src.application.usecases.chats.files.get import Usecase
from src.entrypoints.http.common.deps import read
from src.infrastructure.databases.orm.sqlalchemy.session import Session


def dependency(session: Session = Depends(read)) -> Usecase:
    return Usecase(container=Container(repositories=Repositories(session), security=Security()))
