from src.framework.background import background

from . import pubsub


def workers() -> None:
    background.add(pubsub.run)
