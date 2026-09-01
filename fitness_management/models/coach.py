"""教练相关数据模型。"""
from datetime import date, time
from decimal import Decimal
from typing import Optional

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import mapped_column, Mapped, relationship

from . import Base

class Coach(Base):
    __tablename__ = "coach"
    id: Mapped[int] = mapped_column(primary_key=True, comment="教练编号")
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("user.id", ondelete="SET NULL"),
        nullable=True,
        comment="关联系统登录用户id，可为null"
    )
    name: Mapped[str] = mapped_column(String(64),comment="姓名")
    phone: Mapped[str] = mapped_column(String(64),comment="联系方式")
    specialties: Mapped[str] = mapped_column(String(64),comment="专长")
    salary: Mapped[Optional[Decimal]] = mapped_column(nullable=True, comment="薪资")
    hire_date: Mapped[date] = mapped_column(comment="入职时间")
    status: Mapped[str] = mapped_column(String(64),comment="状态")

    user: Mapped[Optional["User"]] = relationship(back_populates="coach_info")
    # 反向：排班、课程、训练计划
    schedules: Mapped[list["Schedule"]] = relationship(back_populates="coach")
    courses: Mapped[list["Course"]] = relationship(back_populates="coach")
    train_plans: Mapped[list["TrainPlan"]] = relationship(back_populates="coach")


class Schedule(Base):
    __tablename__ = "schedule"
    id: Mapped[int] = mapped_column(primary_key=True, comment="排班编号")
    coach_id: Mapped[int] = mapped_column(
        ForeignKey("coach.id", ondelete="CASCADE"), comment="教练"
    )
    weekday: Mapped[str] = mapped_column(String(64),comment="星期")
    start_time: Mapped[time] = mapped_column(comment="开始时间")
    end_time: Mapped[time] = mapped_column(comment="结束时间")
    status: Mapped[str] = mapped_column(String(64),comment="状态")

    coach: Mapped["Coach"] = relationship(back_populates="schedules")
