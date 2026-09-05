"""教练工作台请求与响应模型。"""
from datetime import date,time
from typing import Optional

from pydantic import BaseModel


class MyScheduleItem(BaseModel):
    """教练排班项"""
    id: int  # 排班项ID
    schedule_date: str  # 排班日期
    working_time: str  # 工作时间
    # start_time: str
    # end_time: str
    course_name: Optional[str] = None  # 课程名称
    location: Optional[str] = None  # 课程地点
    reserve_count: Optional[int] = None  # 预约人数
    status: Optional[str] = None

class AddScheduleItem(BaseModel):
    """添加排班项"""
    coach_id: int  # 教练ID
    # schedule_name: str
    schedule_date: str  # 排班日期
    working_time: str  # 工作时长
    location: Optional[str] = None  # 课程地点


