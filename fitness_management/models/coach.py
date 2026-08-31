"""教练数据模型。"""
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from ..core.database import Base


class Coach(Base):
    """教练档案表。"""

    __tablename__ = "coaches"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), comment="姓名")
    phone: Mapped[str] = mapped_column(String(20), unique=True, comment="手机号")
    specialty: Mapped[str | None] = mapped_column(String(100), default=None, comment="专长：增肌/减脂/瑜伽等")
    status: Mapped[str] = mapped_column(String(20), default="在职", comment="状态：在职/休假/离职")
    hire_date: Mapped[date | None] = mapped_column(Date, default=None, comment="入职日期")
    monthly_hours: Mapped[int] = mapped_column(default=0, comment="月度课时（小时）")
    score: Mapped[float] = mapped_column(Numeric(2, 1), default=5.0, comment="评分（0-5）")
    intro: Mapped[str | None] = mapped_column(String(255), default=None, comment="个人简介")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )
