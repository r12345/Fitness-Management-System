"""器材、报修、盘点和保养模型。"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class EquipmentBase(BaseModel):
    id: int
    name: str
    model: str
    category: str
    location: str
    purchase_date: Optional[datetime] = None
    price: float =None
    status: str = "正常"
    remark: Optional[str] = None
    model_config = ConfigDict(
        from_attributes=True
    )


class EquipmentResponseInfo(BaseModel):
    items: List[EquipmentBase]
    total: int
    page: int
    page_size: int
    total_pages: int

    model_config = ConfigDict(
        from_attributes=True
    )


class EquipmentCreateRequest(BaseModel):
    name: str | None = None
    model: str | None = None
    category: str | None = None
    location: str | None = None
    purchase_date: datetime | None = None
    price: float | None = None
    status: str | None = None
    remark: str | None = None


class EquipmentRepairRequest(BaseModel):
    description: str
    cost: int | None
    repair_time: datetime | None
    remark: str | None


class EquipmentMaintenanceRequest(BaseModel):
    maintenance_time: datetime
    person: str
    content: str