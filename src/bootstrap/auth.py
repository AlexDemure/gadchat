import asyncio

from src.entrypoints.servers.auth import server


async def main() -> None:
    await server(8001)


if __name__ == "__main__":
    asyncio.run(main())
