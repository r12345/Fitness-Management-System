"""教练工作台接口。"""
from typing import List

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from .router import coach_panel_router
from ...core.database import get_db
from ...crud.coach_panel import get_my_schedule, create_schedule
from ...schemas.coach_panel import MyScheduleItem, AddScheduleItem
from ...utils.res import success_response


@coach_panel_router.get('/schedules',response_model=List[MyScheduleItem])
async def get_coach_schedules(
        db: AsyncSession = Depends(get_db),
        coach_id: int = None,
):
    """获取教练排班信息。"""
    data = await get_my_schedule(db, coach_id)
    return success_response(msg="success", data=data)

@coach_panel_router.post('/schedules')
async def post_coach_schedules(

        db: AsyncSession = Depends(get_db),
        schedule: AddScheduleItem = Depends(),
):
    """添加教练排班信息。"""
    data = await create_schedule(db, schedule)
    return success_response(msg="success", data=data)
