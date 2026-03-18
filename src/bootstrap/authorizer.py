import asyncio

from src.entrypoints.servers.authorizer import server


async def main() -> None:
    await server(8000)


if __name__ == "__main__":
    asyncio.run(main())
