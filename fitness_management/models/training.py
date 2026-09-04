"""训练计划、打卡与运动记录相关数据模型。"""
from datetime import date, datetime, time
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base


class TrainPlan(Base):
    """训练计划表，对应 MySQL 的 training_plan。"""

    __tablename__ = "training_plan"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment="计划编号")
    member_id: Mapped[int] = mapped_column(
        ForeignKey("member.id", ondelete="CASCADE"), nullable=False, comment="会员"
    )
    coach_id: Mapped[int] = mapped_column(
        ForeignKey("coach.id", ondelete="CASCADE"), nullable=False, comment="教练"
    )
    goal: Mapped[str] = mapped_column(String(255), nullable=False, comment="训练目标")
    body_part: Mapped[str] = mapped_column(String(128), nullable=False, comment="训练部位")
    actions: Mapped[str] = mapped_column(Text, nullable=False, comment="动作内容")
    sets_reps: Mapped[str] = mapped_column(String(255), nullable=False, comment="组数次数")
    frequency: Mapped[str] = mapped_column(String(128), nullable=False, comment="频率")
    start_date: Mapped[date] = mapped_column(nullable=False, comment="开始日期")
    end_date: Mapped[date] = mapped_column(nullable=False, comment="结束日期")
    remark: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="计划说明")

    member: Mapped["Member"] = relationship(back_populates="train_plans")
    coach: Mapped["Coach"] = relationship(back_populates="train_plans")


class CheckinRecord(Base):
    """到店打卡记录表，对应 MySQL 的 check_in_record。"""

    __tablename__ = "check_in_record"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment="记录编号")
    member_id: Mapped[int] = mapped_column(
        ForeignKey("member.id", ondelete="CASCADE"), nullable=False, comment="会员"
    )
    checkin_date: Mapped[date] = mapped_column(nullable=False, comment="打卡日期")
    checkin_time: Mapped[time] = mapped_column(nullable=False, comment="到店时间")
    leave_time: Mapped[Optional[time]] = mapped_column(nullable=True, comment="离开时间")
    duration: Mapped[Optional[int]] = mapped_column(nullable=True, comment="训练时长")

    member: Mapped["Member"] = relationship(back_populates="checkin_records")


class ExerciseRecord(Base):
    """会员自主运动记录表，对应 MySQL 的 exercise_record。"""

    __tablename__ = "exercise_record"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment="记录编号")
    member_id: Mapped[int] = mapped_column(
        ForeignKey("member.id", ondelete="CASCADE"), nullable=False, comment="会员"
    )
    train_date: Mapped[date] = mapped_column(nullable=False, comment="训练日期")
    content: Mapped[str] = mapped_column(String(255), nullable=False, comment="训练内容")
    weight: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, comment="重量")
    duration_minutes: Mapped[Optional[int]] = mapped_column(nullable=True, comment="训练时长")
    fat_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="体脂率")
    body_weight: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="体重")
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        comment="创建时间"
    )

    member: Mapped["Member"] = relationship(back_populates="exercise_records")
