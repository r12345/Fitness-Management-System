"""训练记录与训练计划数据模型。"""
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from ..core.database import Base


class TrainingRecord(Base):
    """会员训练记录表（会员中心展示）。"""

    __tablename__ = "training_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    member_id: Mapped[int] = mapped_column(
        ForeignKey("members.id", ondelete="CASCADE"), comment="训练会员"
    )
    record_date: Mapped[date] = mapped_column(Date, comment="训练日期")
    content: Mapped[str] = mapped_column(String(100), comment="训练内容，如 肩背力量训练")
    weight: Mapped[str | None] = mapped_column(String(20), default=None, comment="训练重量，如 45kg/自重")
    duration_minutes: Mapped[int | None] = mapped_column(default=None, comment="训练时长（分钟）")
    body_fat: Mapped[float | None] = mapped_column(Numeric(4, 1), default=None, comment="体脂率（%）")
    remark: Mapped[str | None] = mapped_column(String(255), default=None, comment="备注")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment="创建时间")


class TrainingPlan(Base):
    """训练计划表（教练为会员制定）。"""

    __tablename__ = "training_plans"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    member_id: Mapped[int] = mapped_column(
        ForeignKey("members.id", ondelete="CASCADE"), comment="会员"
    )
    coach_id: Mapped[int | None] = mapped_column(
        ForeignKey("coaches.id", ondelete="SET NULL"), default=None, comment="制定教练"
    )
    goal: Mapped[str | None] = mapped_column(String(50), default=None, comment="目标：增肌/减脂/塑形等")
    body_part: Mapped[str | None] = mapped_column(String(100), default=None, comment="训练部位，如 肩背、核心")
    actions: Mapped[str | None] = mapped_column(String(255), default=None, comment="训练动作，如 哑铃划船、平板支撑")
    sets_desc: Mapped[str | None] = mapped_column(String(100), default=None, comment="组次安排，如 4 组 × 12 次")
    frequency: Mapped[str | None] = mapped_column(String(50), default=None, comment="频率，如 每周 3 次")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )
