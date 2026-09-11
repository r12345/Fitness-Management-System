"""预约、取消与签到模型。"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ===== 请求模型 =====

class AppointmentCreate(BaseModel):
    """会员预约课程请求体。"""

    member_id: int = Field(..., description="会员编号")
    course_id: int = Field(..., description="课程编号")
    appointment_time: datetime = Field(..., description="预约时间，如 2026-08-28 18:00:00")


class AppointmentResolve(BaseModel):
    """处理预约冲突请求体。"""

    status: str = Field(..., description="目标预约状态，如 已预约 / 已取消 / 已完成")
    remark: Optional[str] = Field(None, description="处理备注")


# ===== 响应模型 =====

class AppointmentListItem(BaseModel):
    """预约列表项。"""

    id: int
    member_id: int
    member: Optional[str] = None
    phone: Optional[str] = None
    course_id: int
    course: Optional[str] = None
    coach: Optional[str] = None
    appointment_time: datetime
    status: str
    checked_in: Optional[bool] = None
    remark: Optional[str] = None

    class Config:
        from_attributes = True


class AppointmentPageData(BaseModel):
    """预约分页数据。"""

    items: list[AppointmentListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class AppointmentPageResponse(BaseModel):
    """预约分页统一响应。"""

    code: int = 0
    msg: str = "success"
    data: AppointmentPageData
