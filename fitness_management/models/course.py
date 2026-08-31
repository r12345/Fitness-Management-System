"""课程相关数据模型。"""
from sqlalchemy import String, Float, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from . import Base


class Course(Base):
    """10.6 课程表"""
    __tablename__ = "course"
    id: Mapped[int] = mapped_column(primary_key=True, comment="课程编号")
    name: Mapped[str] = mapped_column(String(128), nullable=False, comment="课程名称")
    course_type: Mapped[str] = mapped_column(String(32), nullable=False, comment="团课或私教")
    category: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="分类")
    coach_id: Mapped[int] = mapped_column(ForeignKey("coach.id"), nullable=False, comment="教练")
    start_time: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="上课时间")
    duration: Mapped[int] = mapped_column(Integer, nullable=False, comment="时长")
    max_count: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="最大人数")
    price: Mapped[float] = mapped_column(Float, nullable=False, comment="价格")
    status: Mapped[str] = mapped_column(String(16), nullable=False, comment="状态")
