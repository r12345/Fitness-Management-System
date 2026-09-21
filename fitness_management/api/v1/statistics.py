"""运营数据、教练数据与会员数据统计接口。"""
from typing import Optional

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from .router import statistics_router
from ...core.database import get_db
from ...core.security import get_current_user, require_roles
from ...crud.statistics import get_coaches_statistics, get_members_statistics, get_equipments_statistics, \
    get_current_coach as get_my_coach
from ...models import User
from ...utils.res import success_response


@statistics_router.get('/coaches')
async def get_coach_statistics(
    period: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # 这里的统计口径是「当前登录教练本人」，非教练角色直接返回空数组，不存在越权
    coach = await get_my_coach(db, user)
    if coach is not None:
        coach_info = await get_coaches_statistics(db, period, coach.id)
        return success_response(data=coach_info)
    return success_response(data=[])


@statistics_router.get('/members')
async def get_member_statistics(
    period: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles("admin", "reception")),
):
    member_list = await get_members_statistics(db, period)
    return success_response(data=member_list)


@statistics_router.get('/equipment')
async def get_equipment_statistics(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles("admin", "reception")),
):
    equipment_list = await get_equipments_statistics(db)
    return success_response(data=equipment_list)
