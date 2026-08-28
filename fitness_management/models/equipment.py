"""健身器材、报修与保养相关数据模型。"""
from datetime import date, datetime
from sqlalchemy import String, Date, Float, ForeignKey, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from . import Base


class Equipment(Base):
    """10.10 器材表"""
    __tablename__ = "equipment"
    id: Mapped[int] = mapped_column(primary_key=True, comment="器材编号")
    name: Mapped[str] = mapped_column(String(128), nullable=False, comment="器材名称")
    model: Mapped[str] = mapped_column(String(128), nullable=False, comment="型号")
    category: Mapped[str] = mapped_column(String(64), nullable=False, comment="分类")
    location: Mapped[str] = mapped_column(String(128), nullable=False, comment="存放位置")
    purchase_date: Mapped[date | None] = mapped_column(Date, nullable=True, comment="采购时间")
    price: Mapped[float | None] = mapped_column(Float, nullable=True, comment="价格")
    status: Mapped[str] = mapped_column(String(16), nullable=False, comment="状态")


class EquipmentRepair(Base):
    """10.11 报修表"""
    __tablename__ = "equipment_repair"
    id: Mapped[int] = mapped_column(primary_key=True, comment="报修编号")
    equipment_id: Mapped[int] = mapped_column(ForeignKey("equipment.id"), nullable=False, comment="器材")
    description: Mapped[str] = mapped_column(Text, nullable=False, comment="故障描述")
    cost: Mapped[float | None] = mapped_column(Float, nullable=True, comment="维修费用")
    repair_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="维修时间")
    remark: Mapped[str | None] = mapped_column(Text, nullable=True, comment="维修备注")


class EquipmentMaintenance(Base):
    """10.12 保养记录表"""
    __tablename__ = "equipment_maintenance"
    id: Mapped[int] = mapped_column(primary_key=True, comment="记录编号")
    equipment_id: Mapped[int] = mapped_column(ForeignKey("equipment.id"), nullable=False, comment="器材")
    maintenance_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, comment="保养时间")
    person: Mapped[str] = mapped_column(String(64), nullable=False, comment="保养人")
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="保养内容")
