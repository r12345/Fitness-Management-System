"""教练工作台请求与响应模型。"""
from datetime import date,time
from typing import Optional

from pydantic import BaseModel


class MyScheduleItem(BaseModel):
    """教练排班项"""
    id: int  # 排班项ID
    coach_id: int  # 教练ID
    course_id: int  # 课程ID
    course_name: Optional[str] = None  # 课程名称
    schedule_date: Optional[str] = None  # 排班日期
    start_time: time = None
    end_time: time = None
    location: Optional[str] = None
    booked_count: Optional[int] = None  # 已预约人数
    status: Optional[str] = None  # 状态

    class Config:
        from_attributes = True


class ScheduleCreate(BaseModel):
    """添加排班项"""
    course_id: int  # 课程ID
    schedule_date: date  # 排班日期
    start_time: time = None
    end_time: time = None
    location: Optional[str] = "健身房1"  # 课程地点
    status: Optional[str] = "未开始"

class MyStudentItem(BaseModel):
    """教练学生项"""
    member_id : int  # 学生ID
    name: str = None  # 姓名
    phone: str = None  # 手机号
    goal: str = None  # 目标
    current_plan: Optional[str] = None  # 当前计划
    recent_training: Optional[str] = None  # 最近训练
