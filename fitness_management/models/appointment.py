"""课程预约相关数据模型。"""
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base


class Appointment(Base):
    """课程预约表，对应 MySQL 的 appointment。"""

    __tablename__ = "appointment"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment="预约编号")
    member_id: Mapped[int] = mapped_column(
        ForeignKey("member.id", ondelete="CASCADE"), nullable=False, comment="会员"
    )
    course_id: Mapped[int] = mapped_column(
        ForeignKey("course.id", ondelete="CASCADE"), nullable=False, comment="课程"
    )
    appointment_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, comment="预约时间")
    status: Mapped[str] = mapped_column(String(64), nullable=False, comment="预约状态")
    checked_in: Mapped[Optional[bool]] = mapped_column(
        nullable=True, default=False, comment="是否签到"
    )
    remark: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="处理备注")

    member: Mapped["Member"] = relationship(back_populates="appointments")
    course: Mapped["Course"] = relationship(back_populates="appointments")
