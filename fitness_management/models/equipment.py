"""健身器材、报修与保养相关数据模型。"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, Text

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, relationship, mapped_column


from . import Base

class Equipment(Base):
    __tablename__ = "equipment"
    id: Mapped[int] = mapped_column(primary_key=True, comment="器材编号")
    name: Mapped[str] = mapped_column(String(64),comment="器材名称")
    model: Mapped[str] = mapped_column(String(64),comment="型号")
    category: Mapped[str] = mapped_column(String(64),comment="分类")
    location: Mapped[str] = mapped_column(String(64),comment="存放位置")
    purchase_date: Mapped[Optional[date]] = mapped_column(nullable=True, comment="采购时间")
    price: Mapped[Optional[Decimal]] = mapped_column(nullable=True, comment="价格")
    status: Mapped[str] = mapped_column(String(64),comment="状态")

    repair_list: Mapped[list["Repair"]] = relationship(back_populates="equipment")
    maintain_list: Mapped[list["MaintenanceRecord"]] = relationship(back_populates="equipment")

class Repair(Base):
    __tablename__ = "repair"
    id: Mapped[int] = mapped_column(primary_key=True, comment="报修编号")
    equipment_id: Mapped[int] = mapped_column(
        ForeignKey("equipment.id", ondelete="CASCADE"), comment="器材"
    )
    description: Mapped[str] = mapped_column( String(64),comment="故障描述")
    cost: Mapped[Optional[Decimal]] = mapped_column(nullable=True, comment="维修费用")
    repair_time: Mapped[Optional[datetime]] = mapped_column(nullable=True, comment="维修时间")
    remark: Mapped[Optional[str]] = mapped_column( String(64),nullable=True, comment="维修备注")

    equipment: Mapped["Equipment"] = relationship(back_populates="repair_list")


class MaintenanceRecord(Base):
    __tablename__ = "maintenance_record"
    id: Mapped[int] = mapped_column(primary_key=True, comment="记录编号")
    equipment_id: Mapped[int] = mapped_column(
        ForeignKey("equipment.id", ondelete="CASCADE"), comment="器材"
    )
    maintenance_time: Mapped[datetime] = mapped_column(comment="保养时间")
    person: Mapped[str] = mapped_column(String(64),comment="保养人")
    content: Mapped[str] = mapped_column( String(64),comment="保养内容")

    equipment: Mapped["Equipment"] = relationship(back_populates="maintain_list")