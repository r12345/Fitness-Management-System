"""运营数据、教练数据与会员数据统计接口。"""
from fastapi import Depends
from .router import statistics_router
from ...core.database import get_db
from ...core.security import get_current_user
from ...crud.statistics import get_coaches_statistics, get_members_statistics, get_equipments_statistics, \
    get_current_coach
from ...models import User
from ...schemas.statistics import StatisticsResponse
from ...utils.res import success_response


@statistics_router.get('/coaches')
async def get_coach_statistics(period: str = None,db=Depends(get_db),user:User=Depends(get_current_user)):
    coach = await get_current_coach(db,user)
    if coach is not None:
        coach_info = await get_coaches_statistics(db,period, coach.id)
        return success_response(data=coach_info)
    return success_response(data=[])

@statistics_router.get('/members')
async def get_member_statistics(period: str = None,db=Depends(get_db)):
    member_list = await get_members_statistics(db, period)
    return success_response(data=member_list)

@statistics_router.get('/equipment')
async def get_equipment_statistics(db=Depends(get_db)):
    equipment_list = await get_equipments_statistics(db)
    return success_response(data=equipment_list)
