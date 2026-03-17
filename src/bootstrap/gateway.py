import asyncio

from src.entrypoints.servers.gateway import server


async def main() -> None:
    await server(8003)


if __name__ == "__main__":
    asyncio.run(main())
