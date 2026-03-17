import typing

from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.databases.postgres import postgres


class UsecaseRunner:
    def __init__(self, usecase: typing.Callable[[AsyncSession], typing.Any], transaction: bool) -> None:
        self.usecase = usecase
        self.session = postgres.orm.write if transaction else postgres.orm.read

    async def __call__(self, *args: typing.Any, **kwargs: typing.Any) -> typing.Any:
        async with self.session() as session:
            return await self.usecase(session).execute(*args, **kwargs)
