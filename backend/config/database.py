from sqlalchemy.ext.asyncio import create_async_engine,async_sessionmaker,AsyncSession
from sqlalchemy import text
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+aiomysql://root:123456@localhost/rag?charset=utf8mb4"
)

# 异步数据库引擎
async_engine = create_async_engine(
    DATABASE_URL,
    echo=True,     # 打印SQL
    pool_size=10,
    max_overflow=10
)

# 异步会话工厂
AsyncSession_Local = async_sessionmaker(
    bind=async_engine, # 绑定异步引擎
    expire_on_commit=False, # 提交后会话不自动过期，需要手动关闭
    class_=AsyncSession # 使用异步会话类
)

# 异步会话依赖项
async def get_db():
    async with AsyncSession_Local() as session:
        try:
            yield session # 返回会话
            await session.commit() # 提交事务
        except Exception as e:
            await session.rollback() # 回滚事务
            raise e
        finally:
            await session.close() # 关闭会话
