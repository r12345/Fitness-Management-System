from datetime import datetime, timedelta
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from fitness_management.models import Coach, TrainPlan, Member, Equipment, Course, Appointment, Schedule, User
from fitness_management.crud.member import sync_card_statuses
from fitness_management.schemas.statistics import StatisticsResponse, MemberCardDistributionResponse, \
    MemberStatisticsResponse, EquipmentStatisticsResponse, EquipmentStatus


async def get_coaches_statistics(db: AsyncSession, period: str = None,coach_id: int = None):
    """获取教练统计数据。period可选：today / week / month / year / None(全部)"""
    # 营收口径与教练工作台（crud/coach.py 的 get_coach_statistics_obj）统一为
    # 「该教练名下课程价格合计」。原来这一列取的是 Coach.salary——教练**工资**，
    # 和另一个接口的同名字段口径完全不同，前端拿同一个指标名却看到两套数字。
    course_revenue = (
        select(func.coalesce(func.sum(Course.price), 0.0))
        .where(Course.coach_id == Coach.id)
        .correlate(Coach)
        .scalar_subquery()
    )

    base_select = select(
        Coach.id.label('coach_id'),
        Coach.name.label('coach_name'),
        Coach.hours.label('hours'),
        # distinct 去重：同一个会员多条计划只统计一次
        func.count(func.distinct(TrainPlan.member_id)).label("student_count"),
        course_revenue.label('revenue'),
        func.count(func.distinct(Schedule.id)).label('course_count'),
        func.avg(Coach.score).label('average_score')
    ).outerjoin(Schedule, Schedule.coach_id == Coach.id).where(Coach.id ==coach_id)

    if period:
        now = datetime.now()
        start_time: datetime | None = None
        if period == "today":
            start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "week":
            start_time = now - timedelta(days=7)
        elif period == "month":
            start_time = now - timedelta(days=30)
        elif period == "year":
            start_time = now - timedelta(days=365)

        if start_time:
            # onclause：关联条件 + 时间过滤，放在JOIN ON，保留无计划教练
            query = base_select.join(
                TrainPlan,
                onclause=and_(
                    Coach.id == TrainPlan.coach_id,
                    TrainPlan.start_date >= start_time.date()  # date字段，拿date()
                ),
                isouter=True
            )
        else:
            query = base_select.join(TrainPlan, isouter=True)
    else:
        # period为空，不做时间过滤
        query = base_select.join(TrainPlan, isouter=True)

    # group by 非聚合字段（revenue 是关联子查询，不需要进 group by）
    query = query.group_by(Coach.id, Coach.name, Coach.hours)

    result = await db.execute(query)
    coaches = result.all()
    coach_list = [StatisticsResponse.model_validate(row._mapping) for row in coaches]
    return coach_list




async def get_members_statistics(db: AsyncSession, period: str = None):
    # 先归正卡状态，「在册正常会员」才是真实数字
    await sync_card_statuses(db)

    query= select(func.count(Member.status)).where(Member.status == '正常')
    result = await db.execute(query)
    activate_members = result.scalar_one_or_none()
    if activate_members is None:
        activate_members = 0
    # query1= select(func.count(Member.card_type)).where(Member.card_type== '年卡')
    # query2= select(func.count(Member.card_type)).where(Member.card_type== '季卡')
    # query3= select(func.count(Member.card_type)).where(Member.card_type== '月卡')
    # query4= select(func.count(Member.card_type)).where(Member.card_type== '次卡')
    # result1 = await db.execute(query1)
    # result2 = await db.execute(query2)
    # result3 = await db.execute(query3)
    # result4 = await db.execute(query4)
    # year_card = result1.scalar_one_or_none()
    # if year_card is None:
    #     year_card = 0
    # quarter_card = result2.scalar_one_or_none()
    # if quarter_card is None:
    #     quarter_card = 0
    # month_card = result3.scalar_one_or_none()
    # if month_card is None:
    #     month_card = 0
    # times_card = result4.scalar_one_or_none()
    # if times_card is None:
    #     times_card = 0
    # card_distribution = []
    # card_distribution.append(MemberCardDistributionResponse(card_type='年卡', card_count=year_card))
    # card_distribution.append(MemberCardDistributionResponse(card_type='月卡', card_count=month_card))
    # card_distribution.append(MemberCardDistributionResponse(card_type='季卡', card_count=quarter_card))
    # card_distribution.append(MemberCardDistributionResponse(card_type='次卡', card_count=times_card))
    query = select(Member.card_type, func.count(Member.card_type).label('count')).group_by(Member.card_type)
    result = await db.execute(query)
    card_distribution = [MemberCardDistributionResponse(card_type=row[0], count=row[1]) for row in result.all()]
    return MemberStatisticsResponse(activate_members=activate_members, card_distribution=card_distribution)


async def get_equipments_statistics(db: AsyncSession):

    query1 = select(func.count(Equipment.id))
    result1 = await db.execute(query1)
    total = result1.scalar_one_or_none()
    if total is None:
        total = 0
    query = select(Equipment.status,func.count(Equipment.status)).group_by(Equipment.status)
    result = await db.execute(query)
    rows = result.all()
    status_type = []
    for row in rows:
        status_type.append(EquipmentStatus(status=row[0], count=row[1]))
    return EquipmentStatisticsResponse(total = total, status_type=status_type)


async def get_current_coach(db:AsyncSession,user:User):
    query = select(Coach).where(Coach.user_id == user.id)
    result = await db.execute(query)
    coach = result.scalar_one_or_none()
    return coach
