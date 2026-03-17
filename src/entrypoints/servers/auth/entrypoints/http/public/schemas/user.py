import typing

from src.entrypoints.http.common.schemas import Response
from src.entrypoints.http.public.schemas import Public
from src.infrastructure.databases.postgres.tables import User as _User


class User(Public, Response):
    id: str

    @classmethod
    def serialize(cls, user: _User) -> typing.Self:
        return cls(id=user.id)
