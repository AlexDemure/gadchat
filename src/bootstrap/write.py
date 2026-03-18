import asyncio

from src.entrypoints.servers.write import server


async def main() -> None:
    await server(8004)


if __name__ == "__main__":
    asyncio.run(main())
