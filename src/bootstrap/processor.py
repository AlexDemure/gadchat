import asyncio

from src.entrypoints.workers.processor import worker


async def main() -> None:
    await worker(8002)


if __name__ == "__main__":
    asyncio.run(main())
