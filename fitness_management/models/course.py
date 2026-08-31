"""课程与排课数据模型。"""
from datetime import date, datetime, time

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Time, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.database import Base


class Course(Base):
    """课程表（团课与私教课共用）。"""

    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), comment="课程名称，如 哈他瑜伽")
    category: Mapped[str] = mapped_column(String(50), comment="分类：瑜伽/有氧操/搏击操等")
    course_type: Mapped[str] = mapped_column(String(20), default="团课", comment="类型：团课/私教")
    coach_id: Mapped[int | None] = mapped_column(
        ForeignKey("coaches.id", ondelete="SET NULL"), default=None, comment="授课教练"
    )
    weekday: Mapped[int | None] = mapped_column(default=None, comment="每周固定上课日 1-7（周一至周日），私教课可空")
    start_time: Mapped[time | None] = mapped_column(Time, default=None, comment="开始时间")
    duration_minutes: Mapped[int] = mapped_column(default=60, comment="时长（分钟）")
    max_capacity: Mapped[int] = mapped_column(default=20, comment="最大容量/名额")
    booked_count: Mapped[int] = mapped_column(default=0, comment="已预约人数")
    price: Mapped[float] = mapped_column(Numeric(10, 2), default=0, comment="单价（元），私教课使用")
    status: Mapped[str] = mapped_column(String(20), default="已上架", comment="状态：已上架/已下架")
    description: Mapped[str | None] = mapped_column(String(255), default=None, comment="课程介绍")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )

    coach = relationship("Coach", lazy="joined")


class CourseSchedule(Base):
    """排课表：课程的具体上课场次（教练工作台的排课记录）。"""

    __tablename__ = "course_schedules"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    course_id: Mapped[int | None] = mapped_column(
        ForeignKey("courses.id", ondelete="SET NULL"), default=None, comment="关联课程"
    )
    coach_id: Mapped[int | None] = mapped_column(
        ForeignKey("coaches.id", ondelete="SET NULL"), default=None, comment="授课教练"
    )
    title: Mapped[str] = mapped_column(String(100), comment="场次名称，如 增肌基础课")
    schedule_date: Mapped[date] = mapped_column(Date, comment="上课日期")
    start_time: Mapped[time] = mapped_column(Time, comment="开始时间")
    end_time: Mapped[time] = mapped_column(Time, comment="结束时间")
    location: Mapped[str | None] = mapped_column(String(100), default=None, comment="上课地点，如 团课教室 E1")
    max_capacity: Mapped[int] = mapped_column(default=20, comment="本场次容量")
    booked_count: Mapped[int] = mapped_column(default=0, comment="本场次已约人数")
    status: Mapped[str] = mapped_column(String(20), default="未开始", comment="状态：未开始/已签到/已结束/已取消")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment="创建时间")
