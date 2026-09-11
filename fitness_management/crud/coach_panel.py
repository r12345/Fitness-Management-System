"""教练工作台相关数据库操作（接口文档 §19 / §14）。

教练身份由 API 层从当前登录用户解析后以 ``coach_id`` 传入，
本模块只负责数据读写与业务校验，不感知 HTTP。
"""
from datetime import date as date_type
from typing import Optional

from sqlalchemy import Select, func, select

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from fitness_management.models import (
    Appointment,
    CheckinRecord,
    Coach,
    Course,
    Member,
    Schedule,
    TrainPlan,
)
from fitness_management.schemas.coach_panel import ScheduleCreate
from fitness_management.utils.codes import (
    COACH_SCHEDULE_CONFLICT,
    COURSE_NOT_FOUND,
    HTTP_BAD_REQUEST,
    PERMISSION_DENIED,
)
from fitness_management.utils.res import BizError

#: 计入授课记录的预约状态
TAUGHT_STATUS = ("已完成", "已签到")
#: 已取消的排课不参与时段冲突判断
CANCELED_SCHEDULE_STATUS = ("已取消",)


# ===== 19.1 我的排课 =====

async def get_my_schedules(
    db: AsyncSession,
    coach_id: int,
    status: Optional[str] = None,
    schedule_date: Optional[date_type] = None,
) -> list[dict]:
    """查询指定教练的排课列表（含课程名称），支持按状态与日期筛选。"""
    stmt: Select = (
        select(
            Schedule.id,
            Schedule.coach_id,
            Schedule.course_id,
            Course.name.label("course_name"),
            Schedule.schedule_date,
            Schedule.start_time,
            Schedule.end_time,
            Schedule.location,
            Schedule.booked_count,
            Schedule.status,
        )
        .join(Course, Course.id == Schedule.course_id)
        .where(Schedule.coach_id == coach_id)
    )
    if status:
        stmt = stmt.where(Schedule.status == status)
    if schedule_date:
        stmt = stmt.where(Schedule.schedule_date == schedule_date)

    stmt = stmt.order_by(Schedule.schedule_date.desc(), Schedule.start_time.asc())
    rows = (await db.execute(stmt)).mappings().all()
    return [dict(row) for row in rows]


# ===== 19.2 新增排课 =====

async def _has_schedule_conflict(
    db: AsyncSession, coach_id: int, data: ScheduleCreate
) -> bool:
    """同一教练、同一日期是否存在时段重叠的未取消排课（冲突规则见 §10.2）。"""
    overlap = await db.scalar(
        select(func.count())
        .select_from(Schedule)
        .where(
            Schedule.coach_id == coach_id,
            Schedule.schedule_date == data.schedule_date,
            Schedule.status.notin_(CANCELED_SCHEDULE_STATUS),
            # 两个左闭右开区间重叠的充要条件
            Schedule.start_time < data.end_time,
            Schedule.end_time > data.start_time,
        )
    )
    return bool(overlap)


async def create_my_schedule(db: AsyncSession, coach_id: int, data: ScheduleCreate) -> Schedule:
    """教练为自己新增排课，含课程归属校验与时段冲突校验。"""
    course = await db.scalar(select(Course).where(Course.id == data.course_id))
    if not course:
        raise BizError("课程不存在", code=COURSE_NOT_FOUND, status_code=404)
    # 只能给自己名下的课程排课
    if course.coach_id != coach_id:
        raise BizError("只能为自己名下的课程排课", code=PERMISSION_DENIED, status_code=403)
    if data.end_time <= data.start_time:
        raise BizError("结束时间必须晚于开始时间", code=HTTP_BAD_REQUEST, status_code=400)
    if await _has_schedule_conflict(db, coach_id, data):
        raise BizError("教练排班冲突：该时段已有排课", code=COACH_SCHEDULE_CONFLICT, status_code=400)

    schedule = Schedule(
        coach_id=coach_id,
        course_id=data.course_id,
        schedule_date=data.schedule_date,
        start_time=data.start_time,
        end_time=data.end_time,
        location=data.location,
        booked_count=0,
        status=data.status,
    )
    db.add(schedule)
    await db.flush()
    return schedule


# ===== 19.3 我的学员 =====

async def get_my_students(db: AsyncSession, coach_id: int) -> list[dict]:
    """查询指定教练的学员列表。

    学员 = 在该教练名下存在训练计划的会员；每人取最新的训练计划，
    并带出最近一次到店打卡日期。
    """
    # 每个学员在该教练名下的最新训练计划
    last_plan = (
        select(TrainPlan.member_id, func.max(TrainPlan.id).label("plan_id"))
        .where(TrainPlan.coach_id == coach_id)
        .group_by(TrainPlan.member_id)
        .subquery()
    )
    # 每个学员最近一次到店打卡日期
    last_checkin = (
        select(
            CheckinRecord.member_id,
            func.max(CheckinRecord.checkin_date).label("recent_training"),
        )
        .group_by(CheckinRecord.member_id)
        .subquery()
    )

    plan = aliased(TrainPlan)
    stmt = (
        select(
            Member.id.label("member_id"),
            Member.name,
            Member.phone,
            plan.goal,
            plan.body_part.label("current_plan"),
            last_checkin.c.recent_training,
        )
        .join(last_plan, last_plan.c.member_id == Member.id)
        .join(plan, plan.id == last_plan.c.plan_id)
        .outerjoin(last_checkin, last_checkin.c.member_id == Member.id)
        .order_by(Member.id.asc())
    )
    rows = (await db.execute(stmt)).mappings().all()
    return [dict(row) for row in rows]


# ===== 19.4 授课记录 =====

async def get_my_records(db: AsyncSession, coach: Coach) -> list[dict]:
    """查询指定教练的授课记录。

    :param coach: 教练 ORM 对象，取其 ``score`` 作为每条记录的评分，
        避免 API 层已查过的教练档案被重复查询。

    ``comment`` 取自预约记录上的处理备注——当前数据模型没有独立的课程评价表，
    暂无更细粒度的评分来源。
    """
    score = round(float(coach.score), 1) if coach.score is not None else None

    stmt = (
        select(
            func.date(Appointment.appointment_time).label("date"),
            Course.name.label("course"),
            Member.name.label("student"),
            Course.duration.label("duration"),
            Appointment.remark,
        )
        .join(Course, Course.id == Appointment.course_id)
        .join(Member, Member.id == Appointment.member_id)
        .where(
            Course.coach_id == coach.id,
            Appointment.status.in_(TAUGHT_STATUS),
        )
        .order_by(Appointment.appointment_time.desc())
    )
    rows = (await db.execute(stmt)).mappings().all()
    return [
        {
            "date": row["date"],
            "course": row["course"],
            "student": row["student"],
            "hours": round((row["duration"] or 0) / 60, 1),
            "score": score,
            "comment": row["remark"],
        }
        for row in rows
    ]
