"""会员相关数据库操作。"""
import datetime
from datetime import timedelta



from fitness_management.models import Member, ConsumeRecord, Appointment, CheckinRecord, User
from fitness_management.schemas.member import MemberRequest, RenewMember

# 查看所有会员
# async def show_all_members(page,page_size,db:AsyncSession):
#     offset=(page-1)*page_size
#     query = select(Member).limit(page_size).offset(offset)
#     result = await db.execute(query)
#     members = result.scalars().all()
#     return members
from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

async def show_all_members(page, page_size, keyword, status, card_type, db: AsyncSession):
    limit = page_size
    offset = (page - 1) * page_size
    # 基础查询语句
    stmt = select(Member)

    # 🔹关键词：姓名模糊 OR 手机号模糊，有值才追加条件
    if keyword:
        stmt = stmt.where(
            or_(
                Member.name.like("%" + keyword + "%"),
                Member.phone.like("%" + keyword + "%")
            )
        )
    # 🔹卡状态过滤，有值才追加
    if status:
        stmt = stmt.where(Member.status == status)
    # 🔹办卡类型过滤，有值才追加
    if card_type:
        stmt = stmt.where(Member.card_type == card_type)
    # 🔹统计总条数
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = await db.scalar(count_stmt)
    # 分页
    stmt = stmt.limit(limit).offset(offset)
    result = await db.execute(stmt)
    members = result.scalars().all()

    return members,total


async def get_total(db:AsyncSession):
    query = select(func.count(Member.id))
    result = await db.execute(query)
    total = result.scalar()
    return total
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


async def renew_card(member_id: int,renew_info:RenewMember,db: AsyncSession,user:User):
    query = select(Member).where(Member.id == member_id)
    result = await db.execute(query)
    member = result.scalar_one_or_none()
    if member:
        member.balance += renew_info.amount
        if member.balance >= 0:
            if member.card_expire < datetime.datetime.now().date():
                member.card_expire = datetime.datetime.now() + timedelta(days=30*renew_info.months)
                member.status = '正常'
                member.card_type = renew_info.card_type
                await db.commit()
            else:
                member.card_expire += timedelta(days=30*renew_info.months)
                member.card_type = renew_info.card_type
                await db.commit()
            operator = renew_info.operator
            if operator == '':
                operator = user.name
            consume_record = ConsumeRecord(
                member_id=member.id,
                item=renew_info.remark,
                amount=renew_info.amount,
                pay_method=renew_info.pay_method,
                operator=operator,
                created_at=datetime.datetime.now(),
                member=member
            )
            db.add(consume_record)
            await db.commit()
            await db.refresh(consume_record)
            return [member,consume_record]
        else:
            return None
    else:
        return None

async def getOneMember(member_id: int, db: AsyncSession):
    query = select(Member).where(Member.id == member_id)
    result = await db.execute(query)
    member = result.scalar_one_or_none()
    return member

async def getDetailMember(member_id: int, db: AsyncSession):
        query = select(ConsumeRecord).where(ConsumeRecord.member_id == member_id)
        result = await db.execute(query)
        records = result.scalars().all()
        query2 = select(Appointment).where(Appointment.member_id == member_id)
        result2 = await db.execute(query2)
        appointments = result2.scalars().all()
        query3 = select(CheckinRecord).where(CheckinRecord.member_id == member_id)
        result3 = await db.execute(query3)
        checkins = result3.scalars().all()
        return records,appointments,checkins


# 修改用户
async def updateMember(member_id: int, member: MemberRequest, db: AsyncSession):
    query = select(Member).where(Member.id == member_id)
    result = await db.execute(query)
    member_db = result.scalar_one_or_none()
    if member_db:
        member_db.name = member.name
        member_db.phone = member.phone
        member_db.gender = member.gender
        member_db.age = member.age
        member_db.card_type = member.card_type
        member_db.card_start = member.card_start
        member_db.card_expire = member.card_expire
        member_db.balance = member.balance
        member_db.status = member.status
        member_db.remark = member.remark
        await db.commit()
        return True
    return False


async def updateMemberStatus(id,status,db:AsyncSession):
    query = select(Member).where(Member.id == id)
    result = await db.execute(query)
    member = result.scalar_one_or_none()
    if member:
        member.status = status.status
        await db.commit()
        return True
    return False
