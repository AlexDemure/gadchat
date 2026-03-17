import asyncio

from src.entrypoints.servers.chat import server


async def main() -> None:
    await server(8000)


if __name__ == "__main__":
    asyncio.run(main())
