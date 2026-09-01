"""课程相关数据模型。"""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import ForeignKey, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base
class Course(Base):
    __tablename__ = "course"
    id: Mapped[int] = mapped_column(primary_key=True, comment="课程编号")
    name: Mapped[str] = mapped_column(String(64),comment="课程名称")
    course_type: Mapped[str] = mapped_column(String(64),comment="团课或私教")
    category: Mapped[Optional[str]] = mapped_column(String(64),nullable=True, comment="分类")
    coach_id: Mapped[int] = mapped_column(
        ForeignKey("coach.id", ondelete="CASCADE"), comment="教练"
    )
    start_time: Mapped[Optional[datetime]] = mapped_column(DateTime,nullable=True, comment="上课时间")
    duration: Mapped[int] = mapped_column(comment="时长")
    max_count: Mapped[Optional[int]] = mapped_column(nullable=True, comment="最大人数")
    price: Mapped[Decimal] = mapped_column(comment="价格")
    status: Mapped[str] = mapped_column(String(64),comment="状态")

    coach: Mapped["Coach"] = relationship(back_populates="courses")
    appointments: Mapped[list["Appointment"]] = relationship(back_populates="course")