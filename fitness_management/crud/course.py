"""课程相关数据库操作。"""
from datetime import datetime
from typing import Optional, Tuple

from sqlalchemy import select, func, or_, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from fitness_management.models.course import Course
from fitness_management.models.coach import Coach
from fitness_management.models.appointment import Appointment
from fitness_management.models.member import Member
from fitness_management.schemas.course import CourseCreate, CourseUpdate


async def list_courses(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 10,
    keyword: Optional[str] = None,
    course_type: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    coach_id: Optional[int] = None,
) -> Tuple[list[Course], int]:
    """分页查询课程列表（含教练名）。"""
    stmt = select(Course).options(selectinload(Course.coach))

    # 关键词：课程名称 或 教练姓名
    if keyword:
        stmt = stmt.where(
            or_(
                Course.name.ilike(f"%{keyword}%"),
                Coach.name.ilike(f"%{keyword}%"),
            )
        )

    if course_type:
        stmt = stmt.where(Course.course_type == course_type)
    if category:
        stmt = stmt.where(Course.category == category)
    if status:
        stmt = stmt.where(Course.status == status)
    if coach_id:
        stmt = stmt.where(Course.coach_id == coach_id)

    # 总数
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    # 分页
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    courses = list(result.scalars().unique())

    return courses, total


async def get_course(db: AsyncSession, course_id: int) -> Optional[Course]:
    """按 ID 查单条课程。"""
    stmt = select(Course).where(Course.id == course_id).options(selectinload(Course.coach))
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_course(db: AsyncSession, data: CourseCreate) -> Course:
    """新增课程。"""
    course = Course(**data.model_dump())
    db.add(course)
    await db.flush()
    return course


async def update_course(db: AsyncSession, course_id: int, data: CourseUpdate) -> Optional[Course]:
    """编辑课程（局部更新）。"""
    course = await get_course(db, course_id)
    if not course:
        return None
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(course, key, value)
    await db.flush()
    return course


async def delete_course(db: AsyncSession, course_id: int) -> bool:
    """删除课程。"""
    course = await get_course(db, course_id)
    if not course:
        return False
    await db.delete(course)
    await db.flush()
    return True


async def toggle_course(db: AsyncSession, course_id: int, target_status: str) -> Optional[Course]:
    """课程上下架。"""
    course = await get_course(db, course_id)
    if not course:
        return None
    course.status = target_status
    await db.flush()
    return course


async def get_booked_count(db: AsyncSession, course_id: int) -> int:
    """计算课程已预约人数（状态为 已预约 或 已签到）。"""
    stmt = select(func.count()).select_from(Appointment).where(
        Appointment.course_id == course_id,
        Appointment.status.in_(["已预约", "已签到"]),
    )
    result = await db.execute(stmt)
    return result.scalar_one() or 0


async def get_course_appointments(db: AsyncSession, course_id: int) -> list[Appointment]:
    """查询某课程的全部预约名单（含会员信息）。"""
    stmt = (
        select(Appointment)
        .where(Appointment.course_id == course_id)
        .options(selectinload(Appointment.member))
        .order_by(Appointment.appointment_time.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().unique())
