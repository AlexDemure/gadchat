from src.framework.background import background

from . import redis


def workers() -> None:
    background.add(redis.run)
