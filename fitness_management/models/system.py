"""系统配置、日志与字典相关数据模型。"""
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional,Text
from . import Base
from datetime import datetime

# ------------------------------
# 1. 用户表 user【更新：增加前台反向关系】
# ------------------------------
class User(Base):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(primary_key=True, comment="用户编号")
    username: Mapped[str] = mapped_column(String(64),comment="登录账号")
    password_hash: Mapped[str] = mapped_column(String(256),comment="加密密码")
    role: Mapped[str] = mapped_column(String(64),
        comment="角色标识：super_admin超级管理员,member普通会员,coach教练,reception前台"
    )
    name: Mapped[str] = mapped_column(String(64),comment="姓名")
    phone: Mapped[str] = mapped_column(String(64),comment="手机号")
    status: Mapped[str] = mapped_column(String(64),comment="状态")
    created_at: Mapped[datetime] = mapped_column(comment="创建时间")

    # 一对一：用户绑定会员（仅role=member才会有）
    member: Mapped[Optional["Member"]] = relationship(back_populates="user")
    # 反向：教练表关联到此用户账号
    coach_info: Mapped[Optional["Coach"]] = relationship(back_populates="user")
    # 新增：前台档案反向关联
    reception_info: Mapped[Optional["Reception"]] = relationship(back_populates="user")


class SystemConfig(Base):
    __tablename__ = "sys_config"
    id: Mapped[int] = mapped_column(primary_key=True, comment="配置编号")
    key: Mapped[str] = mapped_column(String(64),nullable=False, comment="配置键")
    value: Mapped[str] = mapped_column(String(64),nullable=False, comment="配置值")
    remark: Mapped[str | None] = mapped_column(String(64),nullable=True, comment="说明")




class SystemLog(Base):
    """10.14 系统日志表"""
    __tablename__ = "sys_log"
    id: Mapped[int] = mapped_column(primary_key=True, comment="日志编号")
    log_type: Mapped[str] = mapped_column(String(64), nullable=False, comment="日志类型")
    user: Mapped[str] = mapped_column( String(64),nullable=False, comment="操作人")
    content: Mapped[str] = mapped_column( String(64),nullable=False, comment="操作内容")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False, comment="时间")


class DictItem(Base):
    """10.15 字典表"""
    __tablename__ = "sys_dict"
    id: Mapped[int] = mapped_column(primary_key=True, comment="字典编号")
    dict_type: Mapped[str] = mapped_column( String(64),nullable=False, comment="字典类型")
    dict_value: Mapped[str] = mapped_column( String(64),nullable=False, comment="字典值")
    status: Mapped[str] = mapped_column( String(64),nullable=False, comment="状态")
