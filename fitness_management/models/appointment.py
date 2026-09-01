"""课程预约相关数据模型。"""
from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base


class Appointment(Base):
    __tablename__ = "appointment"
    id: Mapped[int] = mapped_column(primary_key=True, comment="预约编号")
    member_id: Mapped[int] = mapped_column(
        ForeignKey("member.id", ondelete="CASCADE"), comment="会员"
    )
    course_id: Mapped[int] = mapped_column(
        ForeignKey("course.id", ondelete="CASCADE"), comment="课程"
    )
    appointment_time: Mapped[datetime] = mapped_column(comment="预约时间")
    status: Mapped[str] = mapped_column(String(64),comment="预约状态")
    checked_in: Mapped[Optional[bool]] = mapped_column(nullable=True, comment="是否签到")

    member: Mapped["Member"] = relationship(back_populates="appointments")
    course: Mapped["Course"] = relationship(back_populates="appointments")
