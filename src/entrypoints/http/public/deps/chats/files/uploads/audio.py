from fastapi import Depends

from src.application.usecases.chats.files.uploads.audio import Container
from src.application.usecases.chats.files.uploads.audio import Repository
from src.application.usecases.chats.files.uploads.audio import Security
from src.application.usecases.chats.files.uploads.audio import Storage
from src.application.usecases.chats.files.uploads.audio import Usecase
from src.entrypoints.http.common.deps import write
from src.infrastructure.databases.orm.sqlalchemy.session import Session


def dependency(session: Session = Depends(write)) -> Usecase:
    return Usecase(container=Container(repository=Repository(session), security=Security(), storage=Storage()))
