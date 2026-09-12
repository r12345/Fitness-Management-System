"""前台运营工作台接口。"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from .router import reception_router
from ...core.database import get_db
from ...crud.reception import get_sum, get_re_business_log
from ...utils.res import success_response


@reception_router.get("/summary")
async def get_summary(db: AsyncSession = Depends(get_db)):
    data = await get_sum(db)
    return success_response(data=data)

@reception_router.get("/business-log")
async def get_reception_business_log(db: AsyncSession = Depends(get_db)):
    data = await get_re_business_log(db)
    return success_response(data=data)








