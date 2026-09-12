"""前台运营工作台相关数据库操作。"""
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from fitness_management.models import Member, Appointment, Repair, Reception, ConsumeRecord


async def get_sum(db: AsyncSession):
    # 今日零点
    today_start = datetime(datetime.now().year, datetime.now().month, datetime.now().day)

    # 1. 今日新增会员
    q1 = select(func.count(Member.id)).where(Member.card_start >= today_start)
    today_new_members = (await db.execute(q1)).scalar_one() or 0

    # 2. 待处理预约 (pending状态，根据你实际状态字段值修改)
    q2 = select(func.count(Appointment.id)).where(Appointment.status == "待预约")
    pending_appointments = (await db.execute(q2)).scalar_one() or 0

    # 3. 待处理报修
    q3 = select(func.count(Repair.id))
    pending_repairs = (await db.execute(q3)).scalar_one() or 0

    # 4. 今日营收
    q4 = select(func.sum(ConsumeRecord.amount)).where(ConsumeRecord.created_at >= today_start)
    today_revenue = (await db.execute(q4)).scalar_one() or 0.00

    return {
        "today_new_members": today_new_members,
        "pending_appointments": pending_appointments,
        "pending_repairs": pending_repairs,
        "today_revenue": round(today_revenue,2)
    }


async def get_re_business_log(db: AsyncSession):
    # 查询消费记录，预加载会员，按创建时间倒序（最新在最上面）
    today_start = datetime(datetime.now().year, datetime.now().month, datetime.now().day)
    query = (
        select(ConsumeRecord)
        .options(joinedload(ConsumeRecord.member))
        .where(ConsumeRecord.created_at.between(today_start, datetime.now()))
    )
    result = await db.execute(query)
    record_list = result.scalars().all()

    items = []
    for rec in record_list:
        member_name = rec.member.name if rec.member else ""
        # 只保留时分：10:24
        time_str = rec.created_at.strftime("%H:%M")
        items.append({
            "time": time_str or '0:00',
            "pay_method": rec.pay_method or '未支付',
            "target": member_name or '***',
            "content": f"{rec.item or '****'}，金额 {rec.amount or ''} 元",
            "operator": rec.operator or '***'
        })
    return {"items": items}


