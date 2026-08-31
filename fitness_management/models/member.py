"""会员与会员卡相关数据模型。"""
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from ..core.database import Base


class Member(Base):
    """会员档案表。"""

    __tablename__ = "members"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    member_no: Mapped[str] = mapped_column(String(20), unique=True, comment="会员编号，如 M1001")
    name: Mapped[str] = mapped_column(String(50), comment="姓名")
    phone: Mapped[str] = mapped_column(String(20), unique=True, comment="手机号")
    gender: Mapped[str] = mapped_column(String(10), default="男", comment="性别")
    age: Mapped[int | None] = mapped_column(default=None, comment="年龄")
    card_type: Mapped[str] = mapped_column(String(20), default="月卡", comment="卡种：月卡/季卡/年卡/次卡")
    balance: Mapped[float] = mapped_column(Numeric(10, 2), default=0, comment="账户余额（元）")
    start_date: Mapped[date | None] = mapped_column(Date, default=None, comment="开卡日期")
    expire_date: Mapped[date | None] = mapped_column(Date, default=None, comment="到期日期")
    status: Mapped[str] = mapped_column(String(20), default="正常", comment="状态：正常/暂停/过期")
    remark: Mapped[str | None] = mapped_column(String(255), default=None, comment="备注")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )
