"""SQLAlchemy 数据库连接与会话管理。"""
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# 默认连接本地 MySQL 8.0（utf8mb4），也可通过环境变量覆盖，例如临时切回 SQLite：
# DATABASE_URL=sqlite:///./fitness.db
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://root:root@localhost:3306/fitness?charset=utf8mb4",
)

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=3600)

# 会话工厂：autocommit/autoflush 关闭，保证事务手动提交
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

# 所有 ORM 模型的基类
Base = declarative_base()


def get_db():
    """FastAPI 依赖：请求级数据库会话，请求结束后自动关闭。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
