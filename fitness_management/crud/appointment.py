"""预约相关数据库操作。

业务规则见接口文档 §12：

* 12.1 预约分页列表
* 12.2 会员预约课程 —— 会员状态正常 / 课程已上架 / 课程未满员 / 同一时段不能重复预约
* 12.3 取消预约 —— 已完成不能取消、已取消不能重复取消、取消后释放课程名额
* 12.4 预约签到
* 12.5 处理预约冲突
"""
from datetime import date as date_type
from datetime import datetime, time as time_type, timedelta
from typing import Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from fitness_management.models import Appointment, Coach, Course, Member
from fitness_management.schemas.appointment import AppointmentCreate
from fitness_management.utils.res import BizError

# ===== 状态常量 =====

#: 占用课程名额的预约状态
ACTIVE_STATUS = ("已预约", "已签到")
#: 已完成，不可再取消
FINISHED_STATUS = ("已完成",)
#: 已取消
CANCELED_STATUS = ("已取消",)
#: 可预约的会员卡状态
AVAILABLE_MEMBER_STATUS = ("正常",)
#: 不可预约的课程状态黑名单（兼容文档“已下架/已满员”与历史数据“正常”）
UNBOOKABLE_COURSE_STATUS = ("已下架", "已满员", "停课", "取消", "关闭")
#: 全部合法预约状态
VALID_APPOINTMENT_STATUS = ACTIVE_STATUS + FINISHED_STATUS + CANCELED_STATUS + ("冲突",)


# ===== 内部工具 =====

async def get_appointment(db: AsyncSession, appointment_id: int) -> Optional[Appointment]:
    """按主键查询预约记录。"""
    return await db.scalar(select(Appointment).where(Appointment.id == appointment_id))


def _apply_release_quota(course: Optional[Course], delta: int) -> None:
    """调整课程已预约人数，delta 为正表示占用名额，为负表示释放名额。"""
    if course is None:
        return
    current = course.booked_count or 0
    course.booked_count = max(0, current + delta)


# ===== 12.1 预约分页列表 =====

async def list_appointments(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 10,
    member_id: Optional[int] = None,
    course_id: Optional[int] = None,
    status: Optional[str] = None,
    date_: Optional[date_type] = None,
) -> Tuple[list[dict], int]:
    """分页查询预约列表（含会员、课程、教练名称）。"""
    stmt = (
        select(
            Appointment.id,
            Appointment.member_id,
            Member.name.label("member"),
            Member.phone,
            Appointment.course_id,
            Course.name.label("course"),
            Coach.name.label("coach"),
            Appointment.appointment_time,
            Appointment.status,
            Appointment.checked_in,
            Appointment.remark,
        )
        .join(Member, Member.id == Appointment.member_id)
        .join(Course, Course.id == Appointment.course_id)
        .outerjoin(Coach, Coach.id == Course.coach_id)
    )

    if member_id is not None:
        stmt = stmt.where(Appointment.member_id == member_id)
    if course_id is not None:
        stmt = stmt.where(Appointment.course_id == course_id)
    if status:
        stmt = stmt.where(Appointment.status == status)
    if date_:
        # 用范围查询代替 DATE() 函数，命中 appointment_time 索引
        start = datetime.combine(date_, time_type.min)
        stmt = stmt.where(
            Appointment.appointment_time >= start,
            Appointment.appointment_time < start + timedelta(days=1),
        )

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = (
        stmt.order_by(Appointment.appointment_time.desc(), Appointment.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = (await db.execute(stmt)).mappings().all()
    return [dict(row) for row in rows], total


# ===== 12.2 会员预约课程 =====

async def create_appointment(
    db: AsyncSession,
    data: AppointmentCreate,
    member_id: Optional[int] = None,
) -> Tuple[Appointment, Member, Course]:
    """会员预约课程，返回 (预约记录, 会员, 课程)。"""
    final_member_id = member_id if member_id is not None else data.member_id

    # 1. 会员必须存在且状态正常
    member = await db.scalar(select(Member).where(Member.id == final_member_id))
    if not member:
        raise BizError("会员不存在", code=2001, status_code=404)
    if member.status not in AVAILABLE_MEMBER_STATUS:
        raise BizError(f"会员卡状态为「{member.status}」，不能预约", code=2003, status_code=400)

    # 2. 课程必须存在且处于可预约状态
    course = await db.scalar(select(Course).where(Course.id == data.course_id))
    if not course:
        raise BizError("课程不存在", code=4001, status_code=404)
    if course.status in UNBOOKABLE_COURSE_STATUS:
        raise BizError(f"课程当前状态为「{course.status}」，不可预约", code=4001, status_code=400)

    # 3. 课程未满员（团课看 max_count，私教看 capacity）
    capacity = course.max_count or course.capacity
    if capacity and (course.booked_count or 0) >= capacity:
        raise BizError("课程已满员", code=4002, status_code=400)

    # 4. 同一会员同一时段不能重复预约
    duplicated = await db.scalar(
        select(func.count())
        .select_from(Appointment)
        .where(
            Appointment.member_id == final_member_id,
            Appointment.appointment_time == data.appointment_time,
            Appointment.status.in_(ACTIVE_STATUS + FINISHED_STATUS),
        )
    )
    if duplicated:
        raise BizError("同一时段已存在有效预约", code=4003, status_code=400)

    appointment = Appointment(
        member_id=final_member_id,
        course_id=course.id,
        appointment_time=data.appointment_time,
        status="已预约",
        checked_in=False,
    )
    db.add(appointment)
    # 占用课程名额
    _apply_release_quota(course, 1)
    await db.flush()
    return appointment, member, course


# ===== 12.3 取消预约 =====

async def cancel_appointment(
    db: AsyncSession,
    appointment_id: int,
    member_id: Optional[int] = None,
) -> Appointment:
    """取消预约并释放课程名额。"""
    appointment = await get_appointment(db, appointment_id)
    if not appointment:
        raise BizError("预约不存在", code=404, status_code=404)

    # 会员只能取消自己的预约
    if member_id is not None and appointment.member_id != member_id:
        raise BizError("只能取消本人的预约", code=1003, status_code=403)

    if appointment.status in FINISHED_STATUS:
        raise BizError("已完成的课程不能取消", code=400, status_code=400)
    if appointment.status in CANCELED_STATUS:
        raise BizError("该预约已取消，请勿重复操作", code=400, status_code=400)

    appointment.status = "已取消"
    course = await db.scalar(select(Course).where(Course.id == appointment.course_id))
    _apply_release_quota(course, -1)
    await db.flush()
    return appointment


# ===== 12.4 预约签到 =====

async def checkin_appointment(db: AsyncSession, appointment_id: int) -> Appointment:
    """预约签到。"""
    appointment = await get_appointment(db, appointment_id)
    if not appointment:
        raise BizError("预约不存在", code=404, status_code=404)
    if appointment.status in CANCELED_STATUS:
        raise BizError("已取消的预约不能签到", code=400, status_code=400)
    if appointment.status in FINISHED_STATUS:
        raise BizError("该预约已完成，无需签到", code=400, status_code=400)

    appointment.status = "已签到"
    appointment.checked_in = True
    await db.flush()
    return appointment


# ===== 12.5 处理预约冲突 =====

async def resolve_appointment(
    db: AsyncSession,
    appointment_id: int,
    target_status: str,
    remark: Optional[str] = None,
) -> Appointment:
    """处理预约冲突：修正状态与备注，并同步课程名额。"""
    if target_status not in VALID_APPOINTMENT_STATUS:
        raise BizError(
            f"预约状态不合法，可选：{'、'.join(VALID_APPOINTMENT_STATUS)}",
            code=400,
            status_code=400,
        )

    appointment = await get_appointment(db, appointment_id)
    if not appointment:
        raise BizError("预约不存在", code=404, status_code=404)

    before_active = appointment.status in ACTIVE_STATUS
    after_active = target_status in ACTIVE_STATUS

    appointment.status = target_status
    if remark is not None:
        appointment.remark = remark
    if target_status in CANCELED_STATUS:
        appointment.checked_in = False

    # 状态在“占用名额 / 不占用名额”之间切换时同步课程已预约人数
    if before_active != after_active:
        course = await db.scalar(select(Course).where(Course.id == appointment.course_id))
        _apply_release_quota(course, 1 if after_active else -1)

    await db.flush()
    return appointment
