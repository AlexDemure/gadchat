from src.framework.background import background

from . import delivery


def register() -> None:
    background.add(delivery.listen)
