"""会员个人中心相关数据库操作。"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fitness_management.models import Member


# 通过id 获取会员信息
async def get_member_info_by_id(id:int,db:AsyncSession):
    query = select(Member).where(Member.id == id)
    result = await db.execute(query)
    return result.scalar_one_or_none()

