import asyncio

from src.entrypoints.workers.dispatcher import worker


async def main() -> None:
    await worker()


if __name__ == "__main__":
    asyncio.run(main())
