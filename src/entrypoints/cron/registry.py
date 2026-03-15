from src.infrastructure.scheduling.apscheduler import apscheduler
from src.infrastructure.scheduling.apscheduler.triggers import cron

from . import file


def jobs() -> None:
    if not apscheduler.scheduler:
        return

    apscheduler.add(file.command, cron.everyhour())
