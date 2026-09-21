"""会员个人中心相关数据库操作。"""
from sqlalchemy import select, and_, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from fitness_management.models import Member, Appointment, Course
from fitness_management.schemas.member_center import MemberCenterRequest
from fitness_management.crud.member import sync_card_statuses
from fitness_management.crud.appointment import list_appointments


# 通过id 获取会员信息
async def get_member_info_by_id(id:int,db:AsyncSession):
    query = select(Member).where(Member.user_id == id)
    result = await db.execute(query)
    member = result.scalar_one_or_none()
    if member:
        # 个人中心的卡状态同样要跟到期时间一致：否则会员看到「正常」，
        # 一点预约却被后端按已过期的卡拒掉，两处说法对不上。
        await sync_card_statuses(db, member_id=member.id)
        await db.refresh(member)
    return member


async def get_appointment_by_id(id:int,db:AsyncSession):
    # 复用预约列表查询：同一套逻辑、同一套字段（含同步自教练排课的信息），
    # 会员个人中心的「我的预约」与预约管理页看到的排课信息一致。
    items, _ = await list_appointments(db, member_id=id, page=1, page_size=1000)
    return items


async def get_courses_by_id(id:int,db:AsyncSession):
    query = (
        select(Appointment)
        .options(
            selectinload(Appointment.course).selectinload(Course.coach),
            selectinload(Appointment.schedule),
        )
        .where(and_(Appointment.member_id == id, Appointment.status == '已签到'))
    )
    result = await db.execute(query)
    return result.scalars().all()


async def edit_my_profile(member_info:MemberCenterRequest,member:Member, db:AsyncSession):
    member.name = member_info.name
    member.phone = member_info.phone
    member.height = member_info.height
    member.weight = member_info.weight
    await db.commit()
    await db.refresh(member)
    return member
