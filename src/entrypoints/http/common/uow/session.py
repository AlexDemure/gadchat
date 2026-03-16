import collections.abc
import typing

from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.databases.postgres import postgres


class UnitOfWork:
    def __init__(
        self,
        factory: typing.Callable[[AsyncSession], typing.Any],
        session: typing.Callable[[], collections.abc.AsyncGenerator[AsyncSession, None]],
    ) -> None:
        self.factory = factory
        self.session = session

    async def __call__(self, *args: typing.Any, **kwargs: typing.Any) -> typing.Any:
        async with self.session() as session:
            usecase = self.factory(session)
            return await usecase(*args, **kwargs)


def readable(factory: typing.Callable[[AsyncSession], typing.Any]) -> UnitOfWork:
    return UnitOfWork(factory=factory, session=postgres.orm.read)


def writable(factory: typing.Callable[[AsyncSession], typing.Any]) -> UnitOfWork:
    return UnitOfWork(factory=factory, session=postgres.orm.write)
