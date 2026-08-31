"""器材与维修数据模型。"""
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from ..core.database import Base


class Equipment(Base):
    """器材档案表。"""

    __tablename__ = "equipment"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), comment="器材名称，如 商用跑步机")
    model: Mapped[str | None] = mapped_column(String(50), default=None, comment="型号，如 YJ-8000")
    category: Mapped[str | None] = mapped_column(String(50), default=None, comment="分类：有氧器械/力量器械等")
    location: Mapped[str | None] = mapped_column(String(100), default=None, comment="存放位置，如 有氧区 A1")
    purchase_date: Mapped[date | None] = mapped_column(Date, default=None, comment="购买日期")
    price: Mapped[float] = mapped_column(Numeric(10, 2), default=0, comment="购买价格（元）")
    status: Mapped[str] = mapped_column(String(20), default="正常", comment="状态：正常/维修/报废")
    remark: Mapped[str | None] = mapped_column(String(255), default=None, comment="备注")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment="创建时间")


class EquipmentRepair(Base):
    """器材报修记录表。"""

    __tablename__ = "equipment_repairs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    equipment_id: Mapped[int] = mapped_column(
        ForeignKey("equipment.id", ondelete="CASCADE"), comment="报修器材"
    )
    fault_desc: Mapped[str] = mapped_column(String(255), comment="故障描述")
    reporter: Mapped[str | None] = mapped_column(String(50), default=None, comment="报修人")
    report_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment="报修时间")
    status: Mapped[str] = mapped_column(String(20), default="待处理", comment="状态：待处理/处理中/已完成")
    repair_result: Mapped[str | None] = mapped_column(String(255), default=None, comment="维修结果")
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, default=None, comment="完成时间")
