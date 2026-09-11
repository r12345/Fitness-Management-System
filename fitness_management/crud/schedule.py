"""排班管理（接口文档 §10）相关数据库操作。

.. warning::
   本模块与 :mod:`fitness_management.crud.coach_panel` 存在功能重叠：

   * :func:`get_my_schedule` 与 ``coach_panel.get_my_schedules`` 的查询基本一致
     （后者多支持按状态、日期筛选）；
   * :func:`create_schedule` 与 ``coach_panel.create_my_schedule`` 目标相同，
     但本模块缺少**课程归属校验**与**时段冲突校验**，且用返回 ``None``
     表达失败，与其它 CRUD 抛 ``BizError`` 的风格不一致。

   两者分别服务于 ``/api/v1/schedule/schedules`` 与
   ``/api/v1/coach-panel/schedules``。若确认不再需要两条路由，
   建议删掉本模块、把接口指向 ``crud.coach_panel``。
"""
from typing import Optional

from sqlalchemy import select
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