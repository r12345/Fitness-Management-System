"""系统配置、日志与字典相关数据模型。"""
from datetime import datetime
from sqlalchemy import String, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from . import Base


class User(Base):
    """10.1 用户与角色"""
    __tablename__ = "sys_user"
    id: Mapped[int] = mapped_column(primary_key=True, comment="用户编号")
    username: Mapped[str] = mapped_column(String(64), nullable=False, comment="登录账号")
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False, comment="加密密码")
    role: Mapped[str] = mapped_column(String(32), nullable=False, comment="角色标识")
    name: Mapped[str] = mapped_column(String(64), nullable=False, comment="姓名")
    phone: Mapped[str] = mapped_column(String(20), nullable=False, comment="手机号")
    status: Mapped[str] = mapped_column(String(16), nullable=False, comment="状态")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False, comment="创建时间")


class SystemConfig(Base):
    """10.13 系统配置表"""
    __tablename__ = "sys_config"
    id: Mapped[int] = mapped_column(primary_key=True, comment="配置编号")
    key: Mapped[str] = mapped_column(String(64), nullable=False, comment="配置键")
    value: Mapped[str] = mapped_column(Text, nullable=False, comment="配置值")
    remark: Mapped[str | None] = mapped_column(Text, nullable=True, comment="说明")


class SystemLog(Base):
    """10.14 系统日志表"""
    __tablename__ = "sys_log"
    id: Mapped[int] = mapped_column(primary_key=True, comment="日志编号")
    log_type: Mapped[str] = mapped_column(String(32), nullable=False, comment="日志类型")
    user: Mapped[str] = mapped_column(String(64), nullable=False, comment="操作人")
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="操作内容")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False, comment="时间")


class DictItem(Base):
    """10.15 字典表"""
    __tablename__ = "sys_dict"
    id: Mapped[int] = mapped_column(primary_key=True, comment="字典编号")
    dict_type: Mapped[str] = mapped_column(String(64), nullable=False, comment="字典类型")
    dict_value: Mapped[str] = mapped_column(String(128), nullable=False, comment="字典值")
    status: Mapped[str] = mapped_column(String(16), nullable=False, comment="状态")
