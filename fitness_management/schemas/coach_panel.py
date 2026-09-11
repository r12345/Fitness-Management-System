"""教练工作台请求与响应模型（接口文档 §19 教练工作台 / §14 训练计划）。

教练身份一律由当前登录用户（``role=coach``）推导，请求体不接收 ``coach_id``。

各模型的落点：

    19.1 / 19.2  ScheduleCreate、MyScheduleItem
    19.3         MyStudentItem
    19.4         MyRecordItem
    19.5 / 19.6 / 14.3  MyPlanItem、MemberBrief

.. note::
   日期类型统一以 ``date_type`` 引用 ``datetime.date``：本模块存在名为 ``date``
   的响应字段，若直接写 ``Optional[date]``，字段名会遮蔽同名类型，
   pydantic 解析注解时会把类型认成 ``None``。
"""
from datetime import date as date_type, time
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# ===== 19.1 我的排课 / 19.2 新增排课 =====

class ScheduleCreate(BaseModel):
    """教练新增排课请求体（``coach_id`` 由当前登录用户推导）。"""

    course_id: int = Field(..., description="课程编号")
    schedule_date: date_type = Field(..., description="上课日期")
    start_time: time = Field(..., description="开始时间")
    end_time: time = Field(..., description="结束时间")
    location: str = Field(..., description="上课地点")
    status: str = Field("未开始", description="排课状态")


class MyScheduleItem(BaseModel):
    """我的排课项（同时作为新增排课的响应体）。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    coach_id: int
    course_id: int
    course_name: Optional[str] = Field(None, description="课程名称")
    schedule_date: Optional[date_type] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    location: Optional[str] = None
    booked_count: Optional[int] = 0
    status: Optional[str] = None


# ===== 19.3 我的学员 =====

class MyStudentItem(BaseModel):
    """我的学员项。"""

    model_config = ConfigDict(from_attributes=True)

    member_id: int
    name: Optional[str] = None
    phone: Optional[str] = None
    goal: Optional[str] = Field(None, description="训练目标")
    current_plan: Optional[str] = Field(None, description="当前训练部位")
    recent_training: Optional[date_type] = Field(None, description="最近一次到店日期")


# ===== 19.4 授课记录 =====

class MyRecordItem(BaseModel):
    """授课记录项（字段名 ``date`` 见接口文档 §19.4）。"""

    model_config = ConfigDict(from_attributes=True)

    date: Optional[date_type] = Field(None, description="上课日期")
    course: Optional[str] = Field(None, description="课程名称")
    student: Optional[str] = Field(None, description="学员姓名")
    hours: Optional[float] = Field(None, description="课时数")
    score: Optional[float] = Field(None, description="教练评分")
    comment: Optional[str] = Field(None, description="备注")


# ===== 19.5 / 19.6 / 14.3 训练计划 =====

class MemberBrief(BaseModel):
    """计划关联学员的简要信息。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class MyPlanItem(BaseModel):
    """训练计划项。

    同时给出 ``member_name`` 与嵌套的 ``member``：前者便于表格展示，
    后者兼容前端已使用的 ``item.member.id`` / ``item.member.name``。
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    member_id: int
    member_name: Optional[str] = None
    member: Optional[MemberBrief] = Field(None, description="学员简要信息，兼容前端取值")
    coach_id: int
    goal: str = Field(..., description="训练目标")
    body_part: str = Field(..., description="训练部位")
    actions: str = Field(..., description="训练动作")
    sets_reps: str = Field(..., description="组数与次数")
    frequency: str = Field(..., description="训练频率")
    start_date: date_type
    end_date: date_type
    remark: Optional[str] = None
