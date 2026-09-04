"""会员与会员卡相关数据模型。"""
"""会员与会员卡相关数据模型。"""
from datetime import date
from typing import Optional

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base


class Member(Base):
    """会员表，对应 MySQL 的 member。"""

    __tablename__ = "member"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment="会员编号")
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("sys_user.id", ondelete="SET NULL"),
        nullable=True,
        comment="关联系统登录用户id，线下办卡可为null"
    )
    name: Mapped[str] = mapped_column(String(64), nullable=False, comment="姓名")
    phone: Mapped[str] = mapped_column(String(20), nullable=False, comment="手机号")
    gender: Mapped[Optional[str]] = mapped_column(String(16), nullable=True, comment="性别")
    age: Mapped[Optional[int]] = mapped_column(nullable=True, comment="年龄")
    card_type: Mapped[str] = mapped_column(String(64), nullable=False, comment="办卡类型")
    card_start: Mapped[Optional[date]] = mapped_column(nullable=True, comment="开卡时间")
    card_expire: Mapped[date] = mapped_column(nullable=False, comment="到期时间")
    balance: Mapped[Optional[float]] = mapped_column(nullable=True, default=0, comment="余额")
    status: Mapped[str] = mapped_column(String(16), nullable=False, comment="卡状态")
    remark: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="备注")

    user: Mapped[Optional["User"]] = relationship(back_populates="member")
    # 反向：消费记录、预约、训练计划、打卡
    consume_records: Mapped[list["ConsumeRecord"]] = relationship(back_populates="member")
    appointments: Mapped[list["Appointment"]] = relationship(back_populates="member")
    train_plans: Mapped[list["TrainPlan"]] = relationship(back_populates="member")
    checkin_records: Mapped[list["CheckinRecord"]] = relationship(back_populates="member")
    exercise_records: Mapped[list["ExerciseRecord"]] = relationship(back_populates="member")
