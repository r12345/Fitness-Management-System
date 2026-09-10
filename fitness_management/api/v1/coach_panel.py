"""教练工作台接口。"""
from typing import List

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from .router import coach_panel_router
from ...core.database import get_db
from ...crud.coach_panel import get_my_schedules, create_schedule, get_my_students
from ...schemas.coach_panel import MyScheduleItem, ScheduleCreate
from ...utils.res import success_response


@coach_panel_router.get('/schedules',response_model=List[MyScheduleItem],summary="获取教练排班信息")
async def get_coach_schedules(
        db: AsyncSession = Depends(get_db),
        coach_id: int = None,
):
    """获取教练排班信息。"""
    data = await get_my_schedules(db, coach_id)
    return success_response(msg="获取成功", data=data)

@coach_panel_router.post('/schedules',response_model=MyScheduleItem,summary="添加教练排班信息")
async def post_coach_schedules(
        db: AsyncSession = Depends(get_db),
        coach_id: int = None,
        data: ScheduleCreate = Depends(),
):
    """添加教练排班信息。"""
    data = await create_schedule(db, coach_id, data)
    return success_response(msg="添加成功", data=data)

@coach_panel_router.get("/students")
async def get_students(
        db: AsyncSession = Depends(get_db),
        coach_id: int = None,
):
    """获取教练学生信息。"""
    data = await get_my_students(db, coach_id)
    return success_response(msg="获取成功", data=data)
