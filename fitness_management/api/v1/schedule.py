"""排班管理接口（接口文档 §10）。

    10.x GET    /schedules   当前教练的排课列表
    10.x POST   /schedules   当前教练新增排课

教练身份由 ``get_current_coach`` 依赖解析，与教练工作台共用同一套逻辑，
因此本模块不再自己实现一遍“取当前教练”的判定。

.. note::
   本模块的 ``/api/v1/schedule/schedules`` 与教练工作台的
   ``/api/v1/coach-panel/schedules`` 目前是两条并存的路由，后端逻辑有重叠，
   详见 ``crud/schedule.py`` 顶部说明。
"""
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from fitness_management.api.v1.router import schedule_router
from fitness_management.core.database import get_db
from fitness_management.core.security import get_current_coach
from fitness_management.crud.schedule import create_schedule, get_my_schedule
from fitness_management.models import Coach
from fitness_management.schemas.coach_panel import ScheduleCreate
from fitness_management.utils.res import success_response


@schedule_router.get('/schedules')
async def get_coach_schedules(
    coach: Coach = Depends(get_current_coach),
    db: AsyncSession = Depends(get_db),
):
    """获取当前教练的排课列表。"""
    data = await get_my_schedule(db, coach.id)
    return success_response(data=data)


@schedule_router.post('/schedules')
async def post_coach_schedules(
    schedule: ScheduleCreate,
    coach: Coach = Depends(get_current_coach),
    db: AsyncSession = Depends(get_db),
):
    """当前教练新增排课。"""
    created = await create_schedule(db, coach.id, schedule)
    if created is None:
        raise HTTPException(status_code=400, detail="课程不存在")
    await db.commit()
    return success_response(msg="排课成功", data={
        "id": created.id,
        "coach_id": created.coach_id,
        "course_id": created.course_id,
        "schedule_date": created.schedule_date,
        "start_time": created.start_time,
        "end_time": created.end_time,
        "location": created.location,
        "booked_count": created.booked_count,
        "status": created.status,
    })
