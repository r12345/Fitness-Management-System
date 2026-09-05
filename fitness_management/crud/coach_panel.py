"""教练工作台相关数据库操作。"""
from fastapi import Depends
from sqlalchemy import select, func, insert
from sqlalchemy.ext.asyncio import AsyncSession

from fitness_management.core.database import get_db
from fitness_management.models import Schedule, Course, Coach
from fitness_management.schemas.coach_panel import AddScheduleItem


async def get_my_schedule(db: AsyncSession = Depends(get_db),coach_id: int = None):
    """获取教练排班项"""
    stmt = (
        select(
        Schedule.id,  # 排班项ID
        Course.start_time.label("schedule_start"),  # 排班开始时间
        Schedule.working_time,  # 工作时间
        # Schedule.start_time,  # 课程开始时间
        # Schedule.end_time,  # 课程结束时间
        Course.name.label("course_name"),  # 课程名称
        # Course.location.label("location"),  # 课程地点
        func.count().label("reserve_count"),  # 预约人数
        Schedule.status  # 状态
    )
        .join(Course, Course.coach_id == Schedule.coach_id)
        .where(Schedule.coach_id == coach_id)
        .group_by(Schedule.id, Course.name, Schedule.status)
        .order_by(Schedule.working_time.desc()
        )
    )
    result = await db.execute(stmt)
    rows = result.mappings().all()  # 转换为字典列表
    return rows

def create_schedule(db: AsyncSession, coach_id: int, schedule: AddScheduleItem):
    """创建排班项"""
    pass
