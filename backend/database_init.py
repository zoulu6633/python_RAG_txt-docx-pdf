import asyncio

from config.database import async_engine
from model import Base


async def init_db():

    async with async_engine.begin() as conn:

        # 创建所有表
        await conn.run_sync(
            Base.metadata.create_all
        )


if __name__ == "__main__":
    asyncio.run(init_db())