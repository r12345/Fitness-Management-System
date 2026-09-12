"""SQLAlchemy 数据库连接与会话管理。"""
import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# 数据库连接串，优先读取环境变量，便于本地/测试环境切换
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+aiomysql://root:root@localhost/fitness_management?charset=utf8mb4",
)

async_engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # 打印SQL语句，便于调试
    pool_size=5,  # 连接池大小
    max_overflow=10,  # 超过连接池大小外可创建的最大连接数
)

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,  # 提交后对象属性不过期，避免异步环境下懒加载报错
)


async def get_db() -> AsyncSession:
    """获取异步数据库会话的依赖注入函数。"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()  # 如果没有异常发生，自动提交事务
        except Exception:
            await session.rollback()  # 发生异常时回滚事务
            raise
        finally:
            await session.close()  # 确保最终关闭会话
