"""会员个人中心相关数据库操作。"""
from sqlalchemy import select, and_, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload,selectinload

from fitness_management.models import Member, Appointment, Course
from fitness_management.schemas.member_center import MemberCenterRequest


# 通过id 获取会员信息
async def get_member_info_by_id(id:int,db:AsyncSession):
    query = select(Member).where(Member.user_id == id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_appointment_by_id(id:int,db:AsyncSession):
    query = select(Appointment).options(selectinload(Appointment.course).options(selectinload(Course.coach))).where(Appointment.member_id == id)
    result = await db.execute(query)
    return result.scalars().all()



async def get_courses_by_id(id:int,db:AsyncSession):
    query = (select(Appointment).options(selectinload(Appointment.course).options(selectinload(Course.coach))).where(and_(Appointment.member_id ==id,Appointment.status == '已预约')))
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
