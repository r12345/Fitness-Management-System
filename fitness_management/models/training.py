"""训练计划、打卡与运动记录相关数据模型。"""
from datetime import date, time, datetime
from sqlalchemy import ForeignKey, Date, Time, Integer, Text, String
from sqlalchemy.orm import Mapped, mapped_column
from . import Base


class TrainingPlan(Base):
    """10.8 训练计划表"""
    __tablename__ = "training_plan"
    id: Mapped[int] = mapped_column(primary_key=True, comment="计划编号")
    member_id: Mapped[int] = mapped_column(ForeignKey("member.id"), nullable=False, comment="会员")
    coach_id: Mapped[int] = mapped_column(ForeignKey("coach.id"), nullable=False, comment="教练")
    goal: Mapped[str] = mapped_column(String(255), nullable=False, comment="训练目标")
    body_part: Mapped[str] = mapped_column(String(128), nullable=False, comment="训练部位")
    actions: Mapped[str] = mapped_column(Text, nullable=False, comment="动作内容")
    sets_reps: Mapped[str] = mapped_column(String(255), nullable=False, comment="组数次数")
    frequency: Mapped[str] = mapped_column(String(128), nullable=False, comment="频率")
    start_date: Mapped[date] = mapped_column(Date, nullable=False, comment="开始日期")
    end_date: Mapped[date] = mapped_column(Date, nullable=False, comment="结束日期")


class CheckInRecord(Base):
    """10.9 打卡记录表"""
    __tablename__ = "check_in_record"
    id: Mapped[int] = mapped_column(primary_key=True, comment="记录编号")
    member_id: Mapped[int] = mapped_column(ForeignKey("member.id"), nullable=False, comment="会员")
    checkin_date: Mapped[date] = mapped_column(Date, nullable=False, comment="打卡日期")
    checkin_time: Mapped[time] = mapped_column(Time, nullable=False, comment="到店时间")
    leave_time: Mapped[time | None] = mapped_column(Time, nullable=True, comment="离开时间")
    duration: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="训练时长")
