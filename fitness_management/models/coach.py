"""教练相关数据模型。"""
from datetime import date, time
from sqlalchemy import String, Date, Time, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from . import Base


class Coach(Base):
    """10.4 教练表"""
    __tablename__ = "coach"
    id: Mapped[int] = mapped_column(primary_key=True, comment="教练编号")
    name: Mapped[str] = mapped_column(String(64), nullable=False, comment="姓名")
    phone: Mapped[str] = mapped_column(String(20), nullable=False, comment="联系方式")
    specialties: Mapped[str] = mapped_column(String(255), nullable=False, comment="专长")
    salary: Mapped[float | None] = mapped_column(Float, nullable=True, comment="薪资")
    hire_date: Mapped[date] = mapped_column(Date, nullable=False, comment="入职时间")
    status: Mapped[str] = mapped_column(String(16), nullable=False, comment="状态")


class Schedule(Base):
    """10.5 排班表"""
    __tablename__ = "coach_schedule"
    id: Mapped[int] = mapped_column(primary_key=True, comment="排班编号")
    coach_id: Mapped[int] = mapped_column(ForeignKey("coach.id"), nullable=False, comment="教练")
    weekday: Mapped[str] = mapped_column(String(16), nullable=False, comment="星期")
    start_time: Mapped[time] = mapped_column(Time, nullable=False, comment="开始时间")
    end_time: Mapped[time] = mapped_column(Time, nullable=False, comment="结束时间")
    status: Mapped[str] = mapped_column(String(16), nullable=False, comment="状态")
