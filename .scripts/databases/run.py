import asyncio

import dictionary


async def upload():
    await dictionary.upload()


if __name__ == "__main__":
    asyncio.run(upload())
