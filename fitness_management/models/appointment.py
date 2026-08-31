"""课程预约相关数据模型。"""
from datetime import datetime
from sqlalchemy import ForeignKey, DateTime, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from . import Base


class Appointment(Base):
    """10.7 预约表"""
    __tablename__ = "appointment"
    id: Mapped[int] = mapped_column(primary_key=True, comment="预约编号")
    member_id: Mapped[int] = mapped_column(ForeignKey("member.id"), nullable=False, comment="会员")
    course_id: Mapped[int] = mapped_column(ForeignKey("course.id"), nullable=False, comment="课程")
    appointment_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, comment="预约时间")
    status: Mapped[str] = mapped_column(String(16), nullable=False, comment="预约状态")
    checked_in: Mapped[bool | None] = mapped_column(Boolean, nullable=True, comment="是否签到")
