"""管理员数据大盘接口。"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from .router import dashboard_router
from ...core.database import get_db
from ...crud.dashboard import get_dashboard_sum, get_trend, get_distribution, get_appointments
from ...schemas.dashboard import DashboardSummary
from ...utils.res import success_response


@dashboard_router.get("/summary")
async def get_dashboard_summary(period:str,db: AsyncSession = Depends(get_db)):
    data= await get_dashboard_sum(period,db)
    return success_response(data =DashboardSummary.model_validate(data))



@dashboard_router.get("/trend")
async def get_dashboard_trend(period:str,db: AsyncSession = Depends(get_db)):
    data = await get_trend(period, db)
    return success_response(data=data)


@dashboard_router.get("/card-distribution")
async def get_card_distribution(db: AsyncSession = Depends(get_db)):
    data = await get_distribution( db)
    return success_response(data=data)


@dashboard_router.get("/recent-appointments")
async def get_recent_appointments(db: AsyncSession = Depends(get_db)):
    data = await get_appointments(db)
    return success_response(data=data)



