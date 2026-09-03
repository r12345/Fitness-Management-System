"""健身器材、报修与保养相关数据模型。"""
from datetime import date, datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, relationship, mapped_column

from . import Base


class Equipment(Base):
    """健身器材表，对应 MySQL 的 equipment。"""

    __tablename__ = "equipment"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment="器材编号")
    name: Mapped[str] = mapped_column(String(128), nullable=False, comment="器材名称")
    model: Mapped[str] = mapped_column(String(128), nullable=False, comment="型号")
    category: Mapped[str] = mapped_column(String(64), nullable=False, comment="分类")
    location: Mapped[str] = mapped_column(String(128), nullable=False, comment="存放位置")
    purchase_date: Mapped[Optional[date]] = mapped_column(nullable=True, comment="采购时间")
    price: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="价格")
    status: Mapped[str] = mapped_column(String(16), nullable=False, comment="状态")
    remark: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="备注")

    repair_list: Mapped[list["Repair"]] = relationship(back_populates="equipment")
    maintain_list: Mapped[list["MaintenanceRecord"]] = relationship(back_populates="equipment")


class Repair(Base):
    """器材报修表，对应 MySQL 的 equipment_repair。"""

    __tablename__ = "equipment_repair"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment="报修编号")
    equipment_id: Mapped[int] = mapped_column(
        ForeignKey("equipment.id", ondelete="CASCADE"), nullable=False, comment="器材"
    )
    description: Mapped[str] = mapped_column(Text, nullable=False, comment="故障描述")
    cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="维修费用")
    repair_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, comment="维修时间")
    remark: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="维修备注")

    equipment: Mapped["Equipment"] = relationship(back_populates="repair_list")


class MaintenanceRecord(Base):
    """器材保养记录表，对应 MySQL 的 equipment_maintenance。"""

    __tablename__ = "equipment_maintenance"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment="记录编号")
    equipment_id: Mapped[int] = mapped_column(
        ForeignKey("equipment.id", ondelete="CASCADE"), nullable=False, comment="器材"
    )
    maintenance_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, comment="保养时间")
    person: Mapped[str] = mapped_column(String(64), nullable=False, comment="保养人")
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="保养内容")

    equipment: Mapped["Equipment"] = relationship(back_populates="maintain_list")
