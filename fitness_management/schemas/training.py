"""训练计划、打卡与运动记录模型。"""
from datetime import date, time, datetime
from typing import Optional

from pydantic import BaseModel, Field

from fitness_management.schemas.member import MemberRequest


# ===== 打卡 =====
class CheckinCreate(BaseModel):
    """到店打卡请求。"""
    checkin_time: datetime = Field(..., description="打卡时间，如 2026-08-27 18:42:00")


class LeaveCheckin(BaseModel):
    """离开打卡请求。"""
    leave_time: datetime = Field(..., description="离开时间")


class CheckinItem(BaseModel):
    """打卡记录响应。"""
    id: int
    member_id: int
    checkin_date: date
    checkin_time: time
    leave_time: Optional[time] = None
    duration: Optional[int] = None

    class Config:
        from_attributes = True


class CurrentCheckin(BaseModel):
    """当前在店状态响应（前端刷新后据此恢复「到店/离店」按钮）。"""
    checked_in: bool
    checkin_id: Optional[int] = None
    checkin_date: Optional[date] = None
    checkin_time: Optional[time] = None


# ===== 运动记录 =====
class ExerciseRecordCreate(BaseModel):
    """新增运动记录请求。"""
    member_id: int
    train_date: date
    content: str
    weight: Optional[str] = None
    duration_minutes: Optional[int] = None
    fat_rate: Optional[float] = None
    body_weight: Optional[float] = None


class ExerciseRecordItem(BaseModel):
    """运动记录响应。"""
    id: int
    member_id: int
    train_date: date
    content: str
    weight: Optional[str] = None
    duration_minutes: Optional[int] = None
    fat_rate: Optional[float] = None
    body_weight: Optional[float] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ===== 训练统计 =====
class TrainingStatistics(BaseModel):
    period: str
    training_count: int
    training_minutes: int
    trend: dict


# ===== 训练计划 =====
class PlanCreate(BaseModel):
    """制定训练计划请求。"""
    member_id: int
    goal: str
    body_part: str
    actions: str
    sets_reps: str
    frequency: str
    start_date: date
    end_date: date
    remark: Optional[str] = None


class PlanUpdate(BaseModel):
    """编辑训练计划请求（字段可空）。"""
    goal: Optional[str] = None
    body_part: Optional[str] = None
    actions: Optional[str] = None
    sets_reps: Optional[str] = None
    frequency: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    remark: Optional[str] = None


class MemberItem(BaseModel):
    id: int
    name: str
    class Config:
        from_attributes = True

class PlanItemSelf(BaseModel):
    """训练计划响应。"""
    id: int
    member_id: int
    coach_id: int
    goal: str
    body_part: str
    actions: str
    sets_reps: str
    frequency: str
    start_date: date
    end_date: date
    remark: Optional[str] = None
    member : Optional[MemberItem]

    class Config:
        from_attributes = True

class PlanItem(BaseModel):
    """训练计划响应。"""
    id: int
    member_id: int
    coach_id: int
    goal: str
    body_part: str
    actions: str
    sets_reps: str
    frequency: str
    start_date: date
    end_date: date
    remark: Optional[str] = None

    class Config:
        from_attributes = True

