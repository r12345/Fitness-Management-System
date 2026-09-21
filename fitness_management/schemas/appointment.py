"""预约、取消与签到模型。"""
from datetime import date as date_type
from datetime import datetime, time as time_type
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
    """预约列表项。

    除预约本身字段外，附带「同步自教练排课」的信息：schedule_date / schedule_start /
    schedule_end / schedule_location / schedule_status。这些来自会员预约所关联的那一次排课
    （appointment.schedule_id），会员看到的课程时间、地点、状态与教练工作台完全一致。

    关联不到排课时（排课窗口外的历史预约）这些字段为空，前端退回展示 appointment_time / course。
    """

    id: int
    member_id: int
    member: Optional[str] = None
    phone: Optional[str] = None
    course_id: int
    course: Optional[str] = None
    coach: Optional[str] = None
    schedule_id: Optional[int] = None
    # 同步自教练排课的信息
    schedule_date: Optional[date_type] = None
    schedule_start: Optional[time_type] = None
    schedule_end: Optional[time_type] = None
    schedule_location: Optional[str] = None
    schedule_status: Optional[str] = None
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
