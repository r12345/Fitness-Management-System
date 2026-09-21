"""课程管理相关请求/响应模型。"""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from fitness_management.utils.datetime_parse import format_start_time, format_start_time_input

from .common import to_payload


def _optional_text(value: Optional[str]) -> Optional[str]:
    """可选的文本字段统一收口：去首尾空格，空白串一律当没填（None）。

    地点列刚从无到有，前端又新增了输入框，直接把 "" 落库会让「地点是不是填了」
    变成一个三分状态（None / "" / "三号训练教室"），后面派生排课时还要再判一次。
    在这里收敛成两态，下游只看 None 就行。
    """
    if value is None:
        return None
    text = value.strip()
    return text or None


# ===== 请求模型 =====

class CourseCreate(BaseModel):
    """新增课程请求体。"""
    name: str = Field(..., description="课程名称")
    course_type: str = Field(..., description="团课 group / 私教 private")
    category: Optional[str] = Field(None, description="课程分类")
    location: Optional[str] = Field(None, description="上课地点（教练排课会继承它）")
    coach_id: int = Field(..., description="教练编号")
    start_time: Optional[str] = Field(
        None, description='上课时间，形如 "2026-09-21 18:00:00"；同时决定排课的星期几与时段'
    )
    duration: int = Field(..., description="时长（分钟）")
    max_count: Optional[int] = Field(None, description="最大人数（私教可为空）")
    capacity: Optional[int] = Field(None, description="私教会员名额")
    price: Decimal = Field(..., description="价格")
    status: str = Field("已上架", description="课程状态")

    _normalize_location = field_validator("location")(_optional_text)


class CourseUpdate(BaseModel):
    """编辑课程请求体（所有字段可选）。"""
    name: Optional[str] = None
    course_type: Optional[str] = None
    category: Optional[str] = None
    location: Optional[str] = None
    coach_id: Optional[int] = None
    start_time: Optional[str] = None
    duration: Optional[int] = None
    max_count: Optional[int] = None
    capacity: Optional[int] = None
    price: Optional[Decimal] = None
    status: Optional[str] = None

    _normalize_location = field_validator("location")(_optional_text)


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
    location: Optional[str] = None  # 上课地点；教练排课继承它
    coach_id: int
    coach_name: str
    start_time: Optional[str] = None  # 格式化为 "周X HH:MM"
    start_time_raw: Optional[str] = None  # 编辑回填用 "2026-09-21T18:00"
    duration: int
    max_count: Optional[int]
    capacity: Optional[int] = None
    booked_count: int = 0
    price: Decimal
    status: str

    @classmethod
    def from_course(cls, course, booked_count: int) -> dict:
        """Course ORM → 课程列表项字典。

        booked_count 不是课程表里的列，由调用方查好传进来。

        原先是 api/v1/courses.py 里的私有函数 ``_to_course_list_item``：
        它只负责把 ORM 转成响应体、不碰数据库，属于 schema 的职责。
        """
        return to_payload(cls(
            id=course.id,
            name=course.name,
            course_type=course.course_type,
            category=course.category,
            location=course.location,
            coach_id=course.coach_id,
            coach_name=course.coach.name if course.coach else "",
            # 展示用："周X HH:MM"
            start_time=format_start_time(course.start_time),
            # 编辑回填用：只有它才能直接塞进 <input type="datetime-local">，
            # 直接把 "周三 18:00" 回填进去会让输入框变空、保存时报 500
            start_time_raw=format_start_time_input(course.start_time),
            duration=course.duration,
            max_count=course.max_count,
            capacity=course.capacity,
            booked_count=booked_count,
            price=course.price,
            status=course.status,
        ))


class AppointmentItem(BaseModel):
    """课程预约名单项。"""
    member_id: int
    member: str
    phone: str
    appointment_time: datetime
    status: str
    checked_in: Optional[bool] = None

    @classmethod
    def from_appointment(cls, appointment) -> dict:
        """Appointment ORM → 预约名单项字典。

        原先是 api/v1/courses.py 里手工拼的字典字面量 ——
        那里 import 了本模型却没用上，字段名一旦写错也没有任何校验。
        改成走模型之后，出参形状由这里唯一决定。
        """
        return to_payload(cls(
            member_id=appointment.member_id,
            member=appointment.member.name if appointment.member else "",
            phone=appointment.member.phone if appointment.member else "",
            appointment_time=appointment.appointment_time,
            status=appointment.status,
            checked_in=appointment.checked_in,
        ))


# ===== 分页包装 =====

class PageResp(BaseModel):
    """通用分页响应包装。"""
    items: list
    total: int
    page: int
    page_size: int
    total_pages: int
