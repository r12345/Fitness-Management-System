"""课程预约数据模型。"""
from datetime import date, datetime, time

from sqlalchemy import Date, DateTime, ForeignKey, String, Time, func
from sqlalchemy.orm import Mapped, mapped_column

from ..core.database import Base


class Appointment(Base):
    """课程预约表。"""

    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    member_id: Mapped[int] = mapped_column(
        ForeignKey("members.id", ondelete="CASCADE"), comment="预约会员"
    )
    course_id: Mapped[int | None] = mapped_column(
        ForeignKey("courses.id", ondelete="SET NULL"), default=None, comment="预约课程"
    )
    coach_id: Mapped[int | None] = mapped_column(
        ForeignKey("coaches.id", ondelete="SET NULL"), default=None, comment="授课教练"
    )
    schedule_date: Mapped[date] = mapped_column(Date, comment="预约上课日期")
    start_time: Mapped[time | None] = mapped_column(Time, default=None, comment="上课时间")
    status: Mapped[str] = mapped_column(String(20), default="已预约", comment="状态：已预约/已签到/已完成/已取消")
    checkin_at: Mapped[datetime | None] = mapped_column(DateTime, default=None, comment="签到时间")
    remark: Mapped[str | None] = mapped_column(String(255), default=None, comment="备注")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )
