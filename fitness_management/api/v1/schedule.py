from fastapi import HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fitness_management.api.v1.coach_panel import _get_current_coach
from fitness_management.api.v1.router import schedule_router
from fitness_management.core.database import get_db
from fitness_management.core.security import get_current_user
from fitness_management.crud.schedule import get_my_schedule, create_schedule
from fitness_management.models import User, Coach
from fitness_management.schemas.coach_panel import ScheduleCreate
from fitness_management.utils.res import success_response




@schedule_router.get('/schedules')
async def get_coach_schedules(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """获取当前教练的排课列表。"""
    coach = await _get_current_coach(db, user)
    data = await get_my_schedule(db, coach.id)
    return success_response(data=data)


@schedule_router.post('/schedules')
async def post_coach_schedules(
    schedule: ScheduleCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """当前教练新增排课。"""
    coach = await _get_current_coach(db, user)
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