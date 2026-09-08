"""训练打卡、运动记录、训练统计、训练计划相关数据库操作。"""
from datetime import date, datetime, time, timedelta
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from fitness_management.models import CheckinRecord, ExerciseRecord, TrainPlan, Member, Coach
from fitness_management.schemas.training import (
    CheckinCreate, LeaveCheckin, ExerciseRecordCreate, PlanCreate, PlanUpdate,
)


# ===== 打卡 =====
async def create_checkin(db: AsyncSession, member_id: int, data: CheckinCreate) -> CheckinRecord:
    """到店打卡：拆分 datetime 为 date + time。"""
    record = CheckinRecord(
        member_id=member_id,
        checkin_date=data.checkin_time.date(),
        checkin_time=data.checkin_time.time(),
    )
    db.add(record)
    await db.flush()
    return record


async def leave_checkin(db: AsyncSession, checkin_id: int, member_id: int, data: LeaveCheckin) -> Optional[CheckinRecord]:
    """离开打卡：设置 leave_time 并计算 duration（分钟）。"""
    record = await db.scalar(
        select(CheckinRecord).where(CheckinRecord.id == checkin_id, CheckinRecord.member_id == member_id)
    )
    if not record:
        return None
    record.leave_time = data.leave_time.time()
    # 计算时长：用当日 checkin_time 和 leave_time 差值
    start = datetime.combine(record.checkin_date, record.checkin_time)
    end = datetime.combine(data.leave_time.date(), data.leave_time.time())
    delta = end - start
    record.duration = max(0, int(delta.total_seconds() // 60))
    await db.flush()
    return record


async def list_my_checkins(db: AsyncSession, member_id: int) -> list[CheckinRecord]:
    """我的打卡记录。"""
    result = await db.execute(
        select(CheckinRecord)
        .where(CheckinRecord.member_id == member_id)
        .order_by(CheckinRecord.checkin_date.desc(), CheckinRecord.checkin_time.desc())
    )
    return list(result.scalars().all())


# ===== 运动记录 =====
async def create_exercise_record(db: AsyncSession, data: ExerciseRecordCreate) -> ExerciseRecord:
    record = ExerciseRecord(**data.model_dump())
    db.add(record)
    await db.flush()
    return record


async def list_exercise_records(db: AsyncSession, member_id: Optional[int] = None) -> list[ExerciseRecord]:
    stmt = select(ExerciseRecord)
    if member_id is not None:
        stmt = stmt.where(ExerciseRecord.member_id == member_id)
    stmt = stmt.order_by(ExerciseRecord.train_date.desc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


# ===== 训练统计 =====
async def get_training_statistics(db: AsyncSession, member_id: int, period: str) -> dict:
    """按周/月统计打卡次数和时长，并返回趋势。"""
    today = date.today()
    if period == "week":
        start = today - timedelta(days=today.weekday())  # 本周一
        days = 7
        bucket_labels = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    else:  # month
        start = today.replace(day=1)
        days = (today - start).days + 1
        bucket_labels = [f"第{i}周" for i in range(1, (days + 6) // 7 + 1)]

    # 总打卡数和总时长
    total_stmt = select(
        func.count(CheckinRecord.id),
        func.coalesce(func.sum(CheckinRecord.duration), 0),
    ).where(CheckinRecord.member_id == member_id, CheckinRecord.checkin_date >= start)
    total = await db.execute(total_stmt)
    count, minutes = total.first()

    # 趋势：按天统计次数
    detail_stmt = select(CheckinRecord.checkin_date).where(
        CheckinRecord.member_id == member_id, CheckinRecord.checkin_date >= start
    )
    detail = await db.execute(detail_stmt)
    day_counts: dict[date, int] = {}
    for (d,) in detail.all():
        day_counts[d] = day_counts.get(d, 0) + 1

    if period == "week":
        trend_data = [day_counts.get(start + timedelta(days=i), 0) for i in range(7)]
    else:
        # 按周聚合
        weeks = (days + 6) // 7
        trend_data = [0] * weeks
        for d, cnt in day_counts.items():
            week_idx = (d - start).days // 7
            if 0 <= week_idx < weeks:
                trend_data[week_idx] += cnt

    return {
        "period": period,
        "training_count": int(count or 0),
        "training_minutes": int(minutes or 0),
        "trend": {"categories": bucket_labels[:len(trend_data)], "data": trend_data},
    }


# ===== 训练计划 =====
async def list_my_plans(db: AsyncSession, coach_id: int) -> list[TrainPlan]:
    stmt = (
        select(TrainPlan)
        .options(joinedload(TrainPlan.member))  # ✅一次性把关联Member查出来
        .where(TrainPlan.coach_id == coach_id)
        .order_by(TrainPlan.id.desc())
    )
    result = await db.execute(stmt)
    plans = list(result.scalars().all())
    # 使用：plan.member.member_name
    return plans


async def create_plan(db: AsyncSession, coach_id: int, data: PlanCreate) -> TrainPlan:
    plan = TrainPlan(coach_id=coach_id, **data.model_dump())
    db.add(plan)
    await db.flush()
    return plan


async def update_plan(db: AsyncSession, plan_id: int, coach_id: int, data: PlanUpdate) -> Optional[TrainPlan]:
    plan = await db.scalar(
        select(TrainPlan).where(TrainPlan.id == plan_id, TrainPlan.coach_id == coach_id)
    )
    if not plan:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(plan, field, value)
    await db.flush()
    return plan
