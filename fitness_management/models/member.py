"""会员与会员卡相关数据模型。"""
from datetime import date, datetime

from sqlalchemy import String, Date, Float, Integer,Text
from sqlalchemy.orm import Mapped, mapped_column
from . import Base


class Member(Base):
    """10.2 会员表"""
    __tablename__ = "member"
    id: Mapped[int] = mapped_column(primary_key=True, comment="会员编号")
    name: Mapped[str] = mapped_column(String(64), nullable=False, comment="姓名")
    phone: Mapped[str] = mapped_column(String(20), nullable=False, comment="手机号")
    gender: Mapped[str | None] = mapped_column(String(16), nullable=True, comment="性别")
    age: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="年龄")
    card_type: Mapped[str] = mapped_column(String(64), nullable=False, comment="办卡类型")
    card_start: Mapped[date | None] = mapped_column(Date, nullable=True, comment="开卡时间")
    card_expire: Mapped[date] = mapped_column(Date, nullable=False, comment="到期时间")
    balance: Mapped[float | None] = mapped_column(Float, nullable=True, comment="余额")
    status: Mapped[str] = mapped_column(String(16), nullable=False, comment="卡状态")
    remark: Mapped[str | None] = mapped_column(Text, nullable=True, comment="备注")
