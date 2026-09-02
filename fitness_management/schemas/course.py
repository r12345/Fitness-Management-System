"""课程管理相关请求/响应模型。"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List

from pydantic import BaseModel, Field


# ===== 请求模型 =====

class CourseCreate(BaseModel):
    """新增课程请求体。"""
    name: str = Field(..., description="课程名称")
    course_type: str = Field(..., description="团课 group / 私教 private")
    category: Optional[str] = Field(None, description="课程分类")
    coach_id: int = Field(..., description="教练编号")
    start_time: Optional[datetime] = Field(None, description="上课时间")
    duration: int = Field(..., description="时长（分钟）")
    max_count: Optional[int] = Field(None, description="最大人数（私教可为空）")
    price: Decimal = Field(..., description="价格")
    status: str = Field("已上架", description="课程状态")


class CourseUpdate(BaseModel):
    """编辑课程请求体（所有字段可选）。"""
    name: Optional[str] = None
    course_type: Optional[str] = None
    category: Optional[str] = None
    coach_id: Optional[int] = None
    start_time: Optional[datetime] = None
    duration: Optional[int] = None
    max_count: Optional[int] = None
    price: Optional[Decimal] = None
    status: Optional[str] = None


class CourseToggle(BaseModel):
    """课程上下架请求体。"""
    status: str = Field(..., description="目标状态：已上架 / 已下架")


# ===== 响应模型 =====

class CourseListItem(BaseModel):
    """课程列表项（含动态字段）。"""
    id: int
    name: str
    course_type: str
    category: Optional[str]
    coach_id: int
    coach_name: str
    start_time: Optional[str] = None  # 格式化为 "周X HH:MM"
    duration: int
    max_count: Optional[int]
    booked_count: int = 0
    price: Decimal
    status: str


class AppointmentItem(BaseModel):
    """课程预约名单项。"""
    member_id: int
    member: str
    phone: str
    appointment_time: datetime
    status: str
    checked_in: Optional[bool] = None


# ===== 分页包装 =====

class PageResp(BaseModel):
    """通用分页响应包装。"""
    items: list
    total: int
    page: int
    page_size: int
    total_pages: int
