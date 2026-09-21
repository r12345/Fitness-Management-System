"""课程相关数据模型。"""
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base


class Course(Base):
    """课程表，对应 MySQL 的 course。"""

    __tablename__ = "course"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment="课程编号")
    name: Mapped[str] = mapped_column(String(128), nullable=False, comment="课程名称")
    course_type: Mapped[str] = mapped_column(String(32), nullable=False, comment="团课或私教")
    category: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, comment="分类")
    location: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="上课地点"
    )
    coach_id: Mapped[int] = mapped_column(
        ForeignKey("coach.id", ondelete="CASCADE"), nullable=False, comment="教练"
    )
    start_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="上课时间"
    )
    duration: Mapped[int] = mapped_column(nullable=False, comment="时长")
    max_count: Mapped[Optional[int]] = mapped_column(nullable=True, comment="最大人数")
    capacity: Mapped[Optional[int]] = mapped_column(nullable=True, comment="私教会员名额")
    booked_count: Mapped[int] = mapped_column(default=0, nullable=False, comment="已预约人数")
    price: Mapped[float] = mapped_column(Float, nullable=False, comment="价格")
    status: Mapped[str] = mapped_column(String(16), nullable=False, comment="状态")
    remark: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="课程说明")

    coach: Mapped["Coach"] = relationship(back_populates="courses")
    # passive_deletes=True：这两张子表的外键都是 ON DELETE CASCADE，
    # 删课程时交给数据库去级联，而不是让 ORM 先把子行的 course_id 置成 NULL
    # —— course_id 是 NOT NULL，置空会抛 IntegrityError（表现为「删除课程」直接 500）。
    # 课程现在一建就自动派生排课，所以这条路径天天都会走到。
    appointments: Mapped[list["Appointment"]] = relationship(
        back_populates="course", passive_deletes=True
    )
    schedules: Mapped[list["Schedule"]] = relationship(
        back_populates="course", passive_deletes=True
    )
