"""运营数据、教练数据与会员数据统计接口。"""
from fastapi import Depends

from .router import statistics_router
from ...core.database import get_db
from ...crud.statistics import get_coaches_statistics, get_members_statistics
from ...schemas.statistics import StatisticsResponse
from ...utils.res import success_response


@statistics_router.get('/coaches')
async def get_coach_statistics(period: str = None,db=Depends(get_db)):
    coach_list = await get_coaches_statistics(db,period)
    return success_response(data=coach_list)

@statistics_router.get('/members')
async def get_member_statistics(period: str = None,db=Depends(get_db)):
    member_list = await get_members_statistics(db, period)
    return success_response(data=member_list)
