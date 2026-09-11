"""教练工作台请求与响应模型。"""
from datetime import date, time
from typing import Optional

from pydantic import BaseModel, Field


class ScheduleCreate(BaseModel):
    """新增排课请求体（coach_id 由当前登录用户推导）。"""
    course_id: int = Field(..., description="课程编号")
    schedule_date: date = Field(..., description="上课日期")
    start_time: time = Field(..., description="开始时间")
    end_time: time = Field(..., description="结束时间")
    location: str = Field(..., description="上课地点")
    status: str = Field("未开始", description="排课状态")


class ScheduleItem(BaseModel):
    """排课列表项响应。"""
    id: int
    coach_id: int
    course_id: int
    course_name: Optional[str] = None
    schedule_date: date
    start_time: time
    end_time: time
    location: str
    booked_count: int
    status: str

    class Config:
        from_attributes = True
