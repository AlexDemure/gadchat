import datetime
import functools
import typing

import redis.asyncio

from src.common.formats.utils import hashes
from src.common.formats.utils import json
from src.common.keyboard.collections import SYMBOL_ASTERISK
from src.configuration import settings
from src.framework.routing import APIRouter

from .collections import Namespace
from .collections import Operation


class Redis:
    def __init__(self) -> None:
        self.client: redis.asyncio.Redis | None = None
        self.router = APIRouter(tags=["Cache"])
        self.endpoints()

    async def start(self) -> None:
        self.client = redis.asyncio.from_url(settings.REDIS_HOST, encoding="utf8", decode_responses=True)

        await self.client.ping()  # type:ignore

    async def shutdown(self) -> None:
        await self.client.close()

    async def set(self, key: str, value: typing.Any, expire: int | None = None) -> None:
        await self.client.set(key, json.tostring(value), ex=expire)

    async def get(self, key: str) -> dict[str, typing.Any]:
        data = {}

        if SYMBOL_ASTERISK in key:
            if keys := [key async for _key in self.client.scan_iter(match=key)]:
                if values := await self.client.mget(*keys):
                    for key, value in zip(keys, values):
                        if value:
                            data[key] = json.fromstring(value)
        else:
            if value := await self.client.get(key):
                data[key] = json.fromstring(value)

        return data

    async def delete(self, key: str) -> None:
        if SYMBOL_ASTERISK in key:
            async for _key in self.client.scan_iter(match=key):
                await self.client.delete(_key)
        else:
            await self.client.delete(key)

    def endpoints(self) -> None:
        @self.router.get("/api/-/cache/{key}", description="Get cache")
        async def query(key: str) -> dict[str, typing.Any]:
            return await self.get(key)

        @self.router.delete("/api/-/cache/{key}", description="Delete cache")
        async def command(key: str) -> None:
            await self.delete(key)

    def __call__(
        self,
        operation: Operation,
        namespace: Namespace,
        ttl: datetime.timedelta = datetime.timedelta(minutes=5),
        id: str | None = None,
    ) -> typing.Callable[..., typing.Callable[..., typing.Any]]:
        def decorator(func: typing.Any) -> typing.Callable[..., typing.Awaitable[typing.Any]]:
            @functools.wraps(func)
            async def wrapper(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:
                account = kwargs.get("account")
                context = {key: value for key, value in kwargs.items() if key not in ["account", "usecase"]}
                key = f"{f'{account.id}:' if account else ''}{namespace}:{operation}:{f'{id}:' if id else ''}{hashes.deterministic(func, context)}"
                if cached := await self.get(key):
                    return cached[key]
                else:
                    if (value := await func(*args, **kwargs)) is not None:
                        await self.set(key, value, expire=int(ttl.total_seconds()))
                    return value

            return wrapper

        return decorator

    def invalidate(self, *namespaces: Namespace) -> typing.Callable[..., typing.Callable[..., typing.Any]]:
        def decorator(func: typing.Any) -> typing.Callable[..., typing.Awaitable[typing.Any]]:
            @functools.wraps(func)
            async def wrapper(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:
                user = kwargs.get("user")
                value = await func(*args, **kwargs)
                for namespace in namespaces:
                    await self.delete(f"{namespace}*")
                    await self.delete(f"{user.id if user else ''}:{namespace}*")
                return value

            return wrapper

        return decorator

    async def publish(self, channel: str, payload: dict[str, typing.Any]) -> None:
        await self.client.publish(channel, json.tostring(payload))

    def pubsub(self) -> typing.Any:
        return self.client.pubsub()

    async def sadd(self, key: str, *values: str) -> None:
        if values:
            await self.client.sadd(key, *values)

    async def srem(self, key: str, *values: str) -> None:
        if values:
            await self.client.srem(key, *values)

    async def smembers(self, key: str) -> set[str]:
        return set(await self.client.smembers(key))

    async def sismember(self, key: str, value: str) -> bool:
        return bool(await self.client.sismember(key, value))
