"""系统配置、日志与字典相关数据模型。"""
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base


class User(Base):
    """系统登录用户表，对应 MySQL 的 sys_user。"""

    __tablename__ = "sys_user"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment="用户编号")
    username: Mapped[str] = mapped_column(String(64), nullable=False, comment="登录账号")
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False, comment="加密密码")
    role: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="角色标识：admin超级管理员,reception前台运营,coach健身教练,member普通会员"
    )
    name: Mapped[str] = mapped_column(String(64), nullable=False, comment="姓名")
    phone: Mapped[str] = mapped_column(String(20), nullable=False, comment="手机号")
    status: Mapped[str] = mapped_column(String(16), nullable=False, comment="状态")
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        comment="创建时间"
    )

    member: Mapped[Optional["Member"]] = relationship(back_populates="user")
    coach_info: Mapped[Optional["Coach"]] = relationship(back_populates="user")
    reception_info: Mapped[Optional["Reception"]] = relationship(back_populates="user")


class SystemConfig(Base):
    """系统配置表，对应 MySQL 的 sys_config。"""

    __tablename__ = "sys_config"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment="配置编号")
    key: Mapped[str] = mapped_column(String(64), nullable=False, comment="配置键")
    value: Mapped[str] = mapped_column(Text, nullable=False, comment="配置值")
    remark: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="说明")




class SystemLog(Base):
    """系统日志表，对应 MySQL 的 sys_log。"""

    __tablename__ = "sys_log"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment="日志编号")
    log_type: Mapped[str] = mapped_column(String(32), nullable=False, comment="日志类型")
    user: Mapped[str] = mapped_column(String(64), nullable=False, comment="操作人")
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="操作内容")
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        comment="时间"
    )


class DictItem(Base):
    """字典表，对应 MySQL 的 sys_dict。"""

    __tablename__ = "sys_dict"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment="字典编号")
    dict_type: Mapped[str] = mapped_column(String(64), nullable=False, comment="字典类型")
    dict_value: Mapped[str] = mapped_column(String(128), nullable=False, comment="字典值")
    status: Mapped[str] = mapped_column(String(16), nullable=False, comment="状态")
