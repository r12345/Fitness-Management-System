"""教练相关数据模型。"""
from datetime import date, time
from typing import Optional

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import mapped_column, Mapped, relationship

from . import Base


class Coach(Base):
    """教练表，对应 MySQL 的 coach。"""

    __tablename__ = "coach"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment="教练编号")
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("sys_user.id", ondelete="SET NULL"),
        nullable=True,
        comment="关联系统登录用户id，可为null"
    )
    name: Mapped[str] = mapped_column(String(64), nullable=False, comment="姓名")
    phone: Mapped[str] = mapped_column(String(20), nullable=False, comment="联系方式")
    specialties: Mapped[str] = mapped_column(String(255), nullable=False, comment="专长")
    salary: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="薪资")
    hire_date: Mapped[date] = mapped_column(nullable=False, comment="入职时间")
    status: Mapped[str] = mapped_column(String(16), nullable=False, comment="状态")
    hours: Mapped[int] = mapped_column(default=0, nullable=False, comment="累计授课课时")
    score: Mapped[float] = mapped_column(Float, default=5.0, nullable=False, comment="平均评分")

    user: Mapped[Optional["User"]] = relationship(back_populates="coach_info")
    # 反向：排班、课程、训练计划
    schedules: Mapped[list["Schedule"]] = relationship(back_populates="coach")
    courses: Mapped[list["Course"]] = relationship(back_populates="coach")
    train_plans: Mapped[list["TrainPlan"]] = relationship(back_populates="coach")


class Schedule(Base):
    """教练排班表，对应 MySQL 的 coach_schedule。"""

    __tablename__ = "coach_schedule"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment="排班编号")
    coach_id: Mapped[int] = mapped_column(
        ForeignKey("coach.id", ondelete="CASCADE"), comment="教练"
    )
    weekday: Mapped[str] = mapped_column(String(16), nullable=False, comment="星期")
    start_time: Mapped[time] = mapped_column(nullable=False, comment="开始时间")
    end_time: Mapped[time] = mapped_column(nullable=False, comment="结束时间")
    status: Mapped[str] = mapped_column(String(16), nullable=False, comment="状态")

    coach: Mapped["Coach"] = relationship(back_populates="schedules")
