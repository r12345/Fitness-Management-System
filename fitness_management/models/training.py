"""训练计划、打卡与运动记录相关数据模型。"""
from datetime import time, date
from typing import Optional, Text
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import mapped_column,Mapped,relationship
from . import Base



class TrainPlan(Base):
    __tablename__ = "train_plan"
    id: Mapped[int] = mapped_column(primary_key=True, comment="计划编号")
    member_id: Mapped[int] = mapped_column(
        ForeignKey("member.id", ondelete="CASCADE"), comment="会员"
    )
    coach_id: Mapped[int] = mapped_column(
        ForeignKey("coach.id", ondelete="CASCADE"), comment="教练"
    )
    goal: Mapped[str] = mapped_column(String(64),comment="训练目标")
    body_part: Mapped[str] = mapped_column(String(64),comment="训练部位")
    actions: Mapped[str] = mapped_column(String(64),comment="动作内容")
    sets_reps: Mapped[str] = mapped_column(String(64),comment="组数次数")
    frequency: Mapped[str] = mapped_column(String(64),comment="频率")
    start_date: Mapped[date] = mapped_column(comment="开始日期")
    end_date: Mapped[date] = mapped_column(comment="结束日期")

    member: Mapped["Member"] = relationship(back_populates="train_plans")
    coach: Mapped["Coach"] = relationship(back_populates="train_plans")


class CheckinRecord(Base):
    __tablename__ = "checkin_record"
    id: Mapped[int] = mapped_column(primary_key=True, comment="记录编号")
    member_id: Mapped[int] = mapped_column(
        ForeignKey("member.id", ondelete="CASCADE"), comment="会员"
    )
    checkin_date: Mapped[date] = mapped_column(comment="打卡日期")
    checkin_time: Mapped[time] = mapped_column(comment="到店时间")
    leave_time: Mapped[Optional[time]] = mapped_column(nullable=True, comment="离开时间")
    duration: Mapped[Optional[int]] = mapped_column(nullable=True, comment="训练时长")

    member: Mapped["Member"] = relationship(back_populates="checkin_records")
