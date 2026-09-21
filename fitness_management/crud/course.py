"""课程相关数据库操作。"""
from datetime import datetime
from typing import Optional, Tuple

from fastapi import HTTPException
from sqlalchemy import select, func, or_, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from fitness_management.crud.coach_panel import sync_course_schedules
from fitness_management.models.course import Course
from fitness_management.models.coach import Coach, Schedule
from fitness_management.models.appointment import Appointment
from fitness_management.models.member import Member
from fitness_management.schemas.course import CourseCreate, CourseUpdate
from fitness_management.utils.datetime_parse import parse_start_time
from fitness_management.utils.status import ACTIVE_STATUSES

# 会影响排课的课程字段：改了这几个，已生成的排课要按课程重排一遍。
# 只改价格 / 名称之类时一律不碰排课，免得把教练辛苦调过的时段冲掉。
SCHEDULE_DRIVING_FIELDS = ("start_time", "duration", "location")


async def list_course_locations(db: AsyncSession) -> list[str]:
    """「新增/编辑课程」的上课地点候选。

    取课程表与排课表里出现过的不重复地点：课程的 location 列刚加上，
    此刻多半还是空的；馆里已有的教室名其实都躺在 coach_schedule 里，
    两张表合起来才凑得出完整候选，否则第一次建课时下拉框是空的。

    教练排课会继承课程地点，所以这里同时也是「排课地点」的取值来源。
    """
    rows = list(
        (
            await db.execute(
                select(Course.location)
                .where(Course.location.isnot(None), Course.location != "")
                .distinct()
            )
        ).scalars().all()
    ) + list(
        (
            await db.execute(
                select(Schedule.location)
                .where(Schedule.location.isnot(None), Schedule.location != "")
                .distinct()
            )
        ).scalars().all()
    )
    return sorted({str(r).strip() for r in rows if r and str(r).strip()})


def _safe_parse_start_time(value):
    """解析上课时间，格式不对时抛 400 业务异常，而不是让它冒成 500。"""
    try:
        return parse_start_time(value)
    except ValueError as exc:
        # 全项目统一用 HTTPException（原来这里抛 BizError，会多出一套 {code,msg} 响应体）
        raise HTTPException(status_code=400, detail=str(exc)) from exc


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


def ensure_course_owner(course: Course, owner_coach_id: Optional[int]) -> None:
    """课程写操作的归属校验。

    ``owner_coach_id`` 传 None 表示调用方是管理员/前台，不限归属；
    传了教练 id 就表示「这位教练只能动自己名下的课」。

    以前课程写接口只校验了「是不是教练」，任何教练都能改、能删、
    甚至把别人的课改挂到自己名下 —— 多教练的馆里这是横向越权。
    """
    if owner_coach_id is not None and course.coach_id != owner_coach_id:
        raise HTTPException(status_code=403, detail="只能管理自己名下的课程")


async def create_course(db: AsyncSession, data: CourseCreate, owner_coach_id: Optional[int] = None) -> Course:
    """新增课程，并把它在排课窗口内的排课直接排出来。

    排课不再由教练手工新增，课程一建就该有课表，所以这里顺手派生一次：
    否则教练要等下次打开工作台才看得到，中间那段时间库里是空的。

    教练建课时归属强制是自己 —— 否则他可以借新建把课挂到别人名下。
    """
    payload = data.model_dump()
    # start_time 收的是字符串（可能形如 "周三 18:00"），落库前必须转成 datetime
    payload["start_time"] = _safe_parse_start_time(data.start_time)
    if owner_coach_id is not None:
        payload["coach_id"] = owner_coach_id
    course = Course(**payload)
    db.add(course)
    await db.flush()
    await sync_course_schedules(db, course_ids=[course.id])
    # 显式把 coach 关系读出来。
    # 响应是用 CourseListItem.from_course 拼的，它会取 course.coach；而刚 flush 出来的
    # 对象上这个关系还没加载，响应阶段是同步代码，懒加载一发起就报 MissingGreenlet。
    # 以前只在「请求体里的 coach_id 恰好等于最终归属教练」时侥幸不炸（many-to-one 的
    # 懒加载命中 identity map 就不发 SQL）；教练建课被强制改写归属后这个巧合就没了。
    await db.refresh(course, attribute_names=["coach"])
    return course


async def update_course(
    db: AsyncSession, course_id: int, data: CourseUpdate, owner_coach_id: Optional[int] = None
) -> Optional[Course]:
    """编辑课程（局部更新），必要时重排该课程的排课。"""
    course = await get_course(db, course_id)
    if not course:
        return None
    ensure_course_owner(course, owner_coach_id)
    update_data = data.model_dump(exclude_unset=True)
    # 教练不能借编辑把课程改挂到别人名下（归属是管理员/前台的活）
    if owner_coach_id is not None:
        update_data.pop("coach_id", None)
    if "start_time" in update_data:
        update_data["start_time"] = _safe_parse_start_time(update_data["start_time"])
    for key, value in update_data.items():
        setattr(course, key, value)
    await db.flush()
    # 课程改了上课时间 / 时长 / 地点，已排好的课就过时了 —— 重排一次。
    # 只传这门课的 id，不牵连别的课程；教练改过的日期仍然保留。
    if any(field in update_data for field in SCHEDULE_DRIVING_FIELDS):
        await sync_course_schedules(db, course_ids=[course_id], refresh=True)
    return course


async def delete_course(db: AsyncSession, course_id: int, owner_coach_id: Optional[int] = None) -> bool:
    """删除课程。"""
    course = await get_course(db, course_id)
    if not course:
        return False
    ensure_course_owner(course, owner_coach_id)
    await db.delete(course)
    await db.flush()
    return True


async def toggle_course(
    db: AsyncSession, course_id: int, target_status: str, owner_coach_id: Optional[int] = None
) -> Optional[Course]:
    """课程上下架。"""
    course = await get_course(db, course_id)
    if not course:
        return None
    ensure_course_owner(course, owner_coach_id)
    course.status = target_status
    await db.flush()
    return course


async def get_booked_count(db: AsyncSession, course_id: int) -> int:
    """计算课程已预约人数（未签到 + 已签到，即仍占用名额的预约）。"""
    stmt = select(func.count()).select_from(Appointment).where(
        Appointment.course_id == course_id,
        # 必须包含「待预约」（历史数据用的是这个写法），否则已约人数会少算
        Appointment.status.in_(ACTIVE_STATUSES),
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
