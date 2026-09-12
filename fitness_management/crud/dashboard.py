"""管理员数据大盘相关数据库操作。"""
from datetime import timedelta, datetime

from sqlalchemy import select, func, between
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from fitness_management.models import Member, ConsumeRecord, Appointment


async def get_dashboard_sum(period:str,db: AsyncSession):
    now = datetime.now()

    # 1. 计算周期起点（修正：起点→现在，不是现在→未来）
    if period == "day":
        period_start = datetime(year=now.year, month=now.month, day=now.day)
        period_end = now
    elif period == "week":
        # 本周一0点
        monday = now - timedelta(days=now.weekday())
        period_start = datetime(year=monday.year, month=monday.month, day=monday.day)
        period_end = now
    elif period == "month":
        period_start = datetime(year=now.year, month=now.month, day=1)
        period_end = now
    elif period == "year":
        period_start = datetime(year=now.year, month=1, day=1)
        period_end = now
    else:
        period_start = datetime(year=now.year, month=now.month, day=now.day)
        period_end = now
    stmt1 = select(func.count(Member.id)).where(Member.card_start.between(period_start, period_end))
    stmt2 = select(func.count(Member.id)).where(Member.status == "正常")
    stmt3 = select(func.count(Member.id)).where(Member.status == "过期")
    stmt4 = select(func.sum(ConsumeRecord.amount)).where(ConsumeRecord.created_at.between(period_start, period_end))
    stmt5 = select(func.count(Appointment.id)).where(Appointment.appointment_time.between(period_start, period_end))
    result1 = await db.execute(stmt1)
    result2 = await db.execute(stmt2)
    result3 = await db.execute(stmt3)
    result4 = await db.execute(stmt4)
    result5 = await db.execute(stmt5)
    val1 = result1.scalar() or 0
    val2 = result2.scalar() or 0
    val3 = result3.scalar() or 0
    val4 = result4.scalar() or 0.0  # sum无数据返回None，兜底0.0
    val5 = result5.scalar() or 0

    return {
        'period': period,
        'total_members': val1,
        'new_members': val2,
        'expired_members': val3,
        'total_revenue':val4 ,
        'total_appointments': val5
    }


async def get_trend(period: str, db: AsyncSession):
    now = datetime.now()

    # 1. 计算周期起点（修正：起点→现在，不是现在→未来）
    if period == "day":
        period_start = datetime(year=now.year, month=now.month, day=now.day)
        period_end = now
    elif period == "week":
        # 本周一0点
        monday = now - timedelta(days=now.weekday())
        period_start = datetime(year=monday.year, month=monday.month, day=monday.day)
        period_end = now
    elif period == "month":
        period_start = datetime(year=now.year, month=now.month, day=1)
        period_end = now
    elif period == "year":
        period_start = datetime(year=now.year, month=1, day=1)
        period_end = now
    else:
        period_start = datetime(year=now.year, month=now.month, day=now.day)
        period_end = now

    # 2. 按日期分组统计新增会员
    # MySQL 用 DATE() 函数取日期部分
    member_stmt = (
        select(
            func.date(Member.card_start).label("day"),
            func.count(Member.id).label("cnt")
        )
        .where(Member.card_start.between(period_start, period_end))
        .group_by(func.date(Member.card_start))
    )
    member_result = await db.execute(member_stmt)
    member_map = {str(row.day): row.cnt for row in member_result.all()}

    # 3. 按日期分组统计收入
    revenue_stmt = (
        select(
            func.date(ConsumeRecord.created_at).label("day"),
            func.sum(ConsumeRecord.amount).label("total")
        )
        .where(ConsumeRecord.created_at.between(period_start, period_end))
        .group_by(func.date(ConsumeRecord.created_at))
    )
    revenue_result = await db.execute(revenue_stmt)
    revenue_map = {str(row.day): (row.total or 0) for row in revenue_result.all()}

    # 4. 生成连续的X轴 categories，补齐没有数据的日期为0
    categories = []
    members = []
    revenue = []

    if period == "week":
        # 本周：周一到周日
        weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        for i in range(7):
            day_date = period_start + timedelta(days=i)
            day_str = day_date.strftime("%Y-%m-%d")
            categories.append(weekday_names[i])
            members.append(member_map.get(day_str, 0))
            revenue.append(revenue_map.get(day_str, 0))
    elif period == "month":
        # 本月：1号到今天
        days = (period_end - period_start).days + 1
        for i in range(days):
            day_date = period_start + timedelta(days=i)
            day_str = day_date.strftime("%Y-%m-%d")
            categories.append(f"{day_date.day}日")
            members.append(member_map.get(day_str, 0))
            revenue.append(revenue_map.get(day_str, 0))
    elif period == "year":
        # 本年：1月到12月，按月聚合
        month_member_stmt = (
            select(
                func.date_format(Member.card_start, "%Y-%m").label("month"),
                func.count(Member.id).label("cnt")
            )
            .where(Member.card_start.between(period_start, period_end))
            .group_by(func.date_format(Member.card_start, "%Y-%m"))
        )
        month_member_result = await db.execute(month_member_stmt)
        month_member_map = {row.month: row.cnt for row in month_member_result.all()}

        month_revenue_stmt = (
            select(
                func.date_format(ConsumeRecord.created_at, "%Y-%m").label("month"),
                func.sum(ConsumeRecord.amount).label("total")
            )
            .where(ConsumeRecord.created_at.between(period_start, period_end))
            .group_by(func.date_format(ConsumeRecord.created_at, "%Y-%m"))
        )
        month_revenue_result = await db.execute(month_revenue_stmt)
        month_revenue_map = {row.month: (row.total or 0) for row in month_revenue_result.all()}

        for m in range(1, 13):
            month_str = f"{now.year}-{m:02d}"
            categories.append(f"{m}月")
            members.append(month_member_map.get(month_str, 0))
            revenue.append(month_revenue_map.get(month_str, 0))
    else:
        # day：今天，单天
        day_str = period_start.strftime("%Y-%m-%d")
        categories.append("今天")
        members.append(member_map.get(day_str, 0))
        revenue.append(revenue_map.get(day_str, 0))

    return {
        "period": period,
        "categories": categories,
        "members": members,
        "revenue": revenue
    }


async def get_distribution(db:AsyncSession):
    query = select(Member.card_type,func.count(Member.id)).group_by(Member.card_type).where(Member.status=='正常')
    result = await db.execute(query)
    data = result.all()
    data = [{'card_type':d[0], 'count':d[1]} for d in data]
    return {
        'items':data
    }


async def get_appointments(db: AsyncSession):
    now = datetime.now()
    # 3天前的时间
    three_days_ago = now - timedelta(days=3)
    # 预加载关联的会员、课程，避免N+1查询
    query = (
        select(Appointment)
        .options(
            joinedload(Appointment.member),
            joinedload(Appointment.course)
        )
        .where(Appointment.appointment_time.between(three_days_ago,now))
    )
    result = await db.execute(query)
    appointment_list = result.scalars().all()

    items = []
    for app in appointment_list:
        items.append({
            "member": app.member.name,
            "course": app.course.name,
            "time": app.appointment_time.strftime("%Y-%m-%d %H:%M"),
            "status": app.status
        })
    return {
        "items": items
    }



