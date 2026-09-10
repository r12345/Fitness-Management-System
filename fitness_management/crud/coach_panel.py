"""教练工作台相关数据库操作。"""
from fastapi import Depends
from sqlalchemy import select, func, insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from fitness_management.core.database import get_db
from fitness_management.models import Schedule, Course, Coach, Member, TrainPlan, CheckinRecord
from fitness_management.schemas.coach_panel import ScheduleCreate


async def get_my_schedules(db: AsyncSession = Depends(get_db),coach_id: int = None):
    """获取教练排班信息。"""
    stmt_coach = select(Coach).where(Coach.user_id == coach_id)
    coach = await db.scalar(stmt_coach)
    if not coach:
        return []

    stmt = select(Schedule, Course).join(Course, Schedule.course_id == Course.id).where(Schedule.coach_id == coach.id)
    rows = await db.execute(stmt)
    rows = rows.mappings().all()  # 转换为字典列表
    return rows

async def create_schedule(db: AsyncSession = Depends(get_db), coach_id: int = None, data: ScheduleCreate = Depends()):
    """添加教练排班信息。"""
    stmt_coach = select(Coach).where(Coach.user_id == coach_id)
    coach = await db.scalar(stmt_coach)
    if not coach:
        return {"msg": "教练不存在"}
    new_sch = Schedule(
        coach_id=coach.id,
        **data.model_dump(),  # 转换为字典
    )
    db.add(new_sch)
    await db.commit()
    await db.refresh(new_sch)
    return new_sch

async def get_my_students(db: AsyncSession = Depends(get_db), coach_id: int = None):
    """获取教练学生信息。"""
    # 查询学员最新的训练计划
    last_training_plan = (select(
        TrainPlan.member_id,
        func.max(TrainPlan.id).label("plan_id")  # 最新的训练记录ID
    )
    .where(TrainPlan.coach_id == coach_id)  # 筛选出教练的训练记录
    .group_by(TrainPlan.member_id)  # 按相同的学员ID分组
    .subquery())  # 把子查询语句，封装成一张临时虚拟表，可以在外层 select 中 join 使用。


    # 查询每个学员的最新训练日期
    last_training_time = (select(
        CheckinRecord.member_id,
        func.max(CheckinRecord.checkin_date).label("last_data")  # 最新的训练日期
    )
    .group_by(CheckinRecord.member_id)  # 按相同的学员ID分组
    .subquery())  # 把子查询语句，封装成一张临时虚拟表，可以在外层 select 中 join 使用。

    # 原始训练计划表
    TrainPlan2 = aliased(TrainPlan)  # 创建第二个别名 aliased 用于在 join 中引用不同的表

    stmt = (select(
        Member.id.label("member_id"),
        Member.name,
        Member.phone,
        TrainPlan2.goal,
        TrainPlan2.body_part.label("current_plan"),  # 当前计划
        # last_training_time.last_data.label("recent_training"),  # 最近训练日期
        last_training_time.c.last_data.label("recent_training"),  # 子查询必须使用 c. 来引用字段
    )
    .join(last_training_plan, last_training_plan.c.member_id == Member.id)  # 加入最新的训练计划
    .join(TrainPlan2, TrainPlan2.id == last_training_plan.c.plan_id)  # 加入最新的训练日期
    .outerjoin(last_training_time, last_training_time.c.member_id == Member.id)  # 加入最新的训练日期
    )
    result = await db.execute(stmt)
    rows = result.mappings().all()  # 转换为字典列表
    return rows
