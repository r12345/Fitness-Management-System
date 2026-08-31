"""系统用户、配置与操作日志数据模型。"""
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from ..core.database import Base


class SysUser(Base):
    """系统账号表：管理员/前台/教练/会员统一登录账号。"""

    __tablename__ = "sys_users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, comment="登录用户名")
    password_hash: Mapped[str] = mapped_column(String(255), comment="密码哈希（passlib bcrypt）")
    real_name: Mapped[str] = mapped_column(String(50), comment="真实姓名")
    role: Mapped[str] = mapped_column(String(20), comment="角色：admin/reception/coach/member")
    ref_id: Mapped[int | None] = mapped_column(default=None, comment="关联业务 id：教练 id 或会员 id")
    status: Mapped[str] = mapped_column(String(20), default="启用", comment="状态：启用/禁用")
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, default=None, comment="最后登录时间")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment="创建时间")


class SysConfig(Base):
    """系统配置表：键值对形式的系统参数。"""

    __tablename__ = "sys_configs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(100), unique=True, comment="配置键，如 gym.name")
    value: Mapped[str] = mapped_column(String(255), comment="配置值")
    remark: Mapped[str | None] = mapped_column(String(255), default=None, comment="说明")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )


class SysOperLog(Base):
    """操作日志表：数据大盘的最近动态展示。"""

    __tablename__ = "sys_oper_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    operator: Mapped[str] = mapped_column(String(50), comment="操作人，如 前台小周")
    module: Mapped[str | None] = mapped_column(String(50), default=None, comment="操作模块：会员/课程/器材等")
    content: Mapped[str] = mapped_column(String(255), comment="操作内容")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment="操作时间")
