"""会员相关数据库操作。"""
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fitness_management.models import Member
from fitness_management.schemas.member import MemberRequest


# 查看所有会员
# async def show_all_members(page,page_size,db:AsyncSession):
#     offset=(page-1)*page_size
#     query = select(Member).limit(page_size).offset(offset)
#     result = await db.execute(query)
#     members = result.scalars().all()
#     return members
async def show_all_members(db:AsyncSession):
    query = select(Member)
    result = await db.execute(query)
    members = result.scalars().all()
    return members
# 创建用户
async def add_member(member: MemberRequest, db: AsyncSession):
    member = Member(
        name=member.name,
        phone=member.phone,
        gender=member.gender,
        age=member.age,
        card_type=member.card_type,
        card_start=member.card_start,
        card_expire=member.card_expire,
        balance=member.balance,
        status=member.status,
        remark=member.remark,
        )
    db.add(member)
    await db.commit()
    await db.refresh(member)
    return member

async def delete_member(member_id: int, db: AsyncSession):
    query = select(Member).where(Member.id == member_id)
    result = await db.execute(query)
    member = result.scalar()
    if member:
        await db.delete(member)
        await db.commit()
        return True
    else:
        return False


async def renew_card(member_id: int,renew:float, db: AsyncSession):
    query = select(Member).where(Member.id == member_id)
    result = await db.execute(query)
    member = result.scalar_one_or_none()
    if member:
        member.balance += renew
        if member.balance >= 0:
            member.card_expire = member.card_expire + timedelta(days=365)
            member.status='正常'
            await db.commit()
            return True
        else:
            return False
    else:
        return False

