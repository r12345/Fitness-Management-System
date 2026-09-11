"""课程相关数据模型。"""
from typing import Optional

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base


class Course(Base):
    """课程表，对应 MySQL 的 course。"""

    __tablename__ = "course"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment="课程编号")
    name: Mapped[str] = mapped_column(String(128), nullable=False, comment="课程名称")
    course_type: Mapped[str] = mapped_column(String(32), nullable=False, comment="团课或私教")
    category: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, comment="分类")
    coach_id: Mapped[int] = mapped_column(
        ForeignKey("coach.id", ondelete="CASCADE"), nullable=False, comment="教练"
    )
    # 数据库中该列实际为 varchar(64)，取值形如 "周一 19:30" 或 "19:30:00"
    start_time: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, comment="上课时间")
    duration: Mapped[int] = mapped_column(nullable=False, comment="时长")
    max_count: Mapped[Optional[int]] = mapped_column(nullable=True, comment="最大人数")
    capacity: Mapped[Optional[int]] = mapped_column(nullable=True, comment="私教会员名额")
    booked_count: Mapped[int] = mapped_column(default=0, nullable=False, comment="已预约人数")
    price: Mapped[float] = mapped_column(Float, nullable=False, comment="价格")
    status: Mapped[str] = mapped_column(String(16), nullable=False, comment="状态")
    remark: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="课程说明")

    coach: Mapped["Coach"] = relationship(back_populates="courses")
    appointments: Mapped[list["Appointment"]] = relationship(back_populates="course")
    schedules: Mapped[list["Schedule"]] = relationship(back_populates="course")
