"""教练工作台相关数据库操作。"""
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from fitness_management.models import Schedule, Course, Coach
from fitness_management.schemas.coach_panel import ScheduleCreate


async def get_my_schedule(db: AsyncSession, coach_id: int) -> list[dict]:
    """获取教练的排课列表（含课程名、预约人数）。"""
    stmt = (
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
        .order_by(Schedule.schedule_date.desc(), Schedule.start_time.asc())
    )
    result = await db.execute(stmt)
    return [dict(row) for row in result.mappings().all()]


async def create_schedule(db: AsyncSession, coach_id: int, data: ScheduleCreate) -> Optional[Schedule]:
    """新增排课（coach_id 由调用方传入）。"""
    # 校验教练存在
    coach = await db.scalar(select(Coach).where(Coach.id == coach_id))
    if not coach:
        return None
    # 校验课程存在
    course = await db.scalar(select(Course).where(Course.id == data.course_id))
    if not course:
        return None

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
