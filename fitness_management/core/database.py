"""SQLAlchemy 数据库连接与会话管理。"""
from sqlalchemy.ext.asyncio import create_async_engine

# 创建异步引擎
from sqlalchemy.ext.asyncio import create_async_engine
from fastapi import Depends
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

# 假设使用 asyncpg 作为 PostgreSQL 的异步驱动
DATABASE_URL = "mysql+aiomysql://root:root@localhost/fitness_management?charset=utf8mb4"

async_engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # 打印SQL语句，便于调试
    pool_size=5, # 连接池大小
    max_overflow=10 # 超过连接池大小外可创建的最大连接数
)


# 创建异步会话工厂

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False # 提交后对象属性不过期，避免异步环境下懒加载报错
)

# 创建数据库依赖注入


async def get_db() -> AsyncSession:
    """
    获取异步数据库会话的依赖注入函数
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit() # 如果没有异常发生，自动提交事务
        except Exception:
            await session.rollback() # 发生异常时回滚事务
            raise
        finally:
            await session.close() # 确保最终关闭会话
