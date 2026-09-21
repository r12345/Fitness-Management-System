"""预约相关数据库操作。"""
from datetime import date as date_type
from datetime import datetime, time as time_type, timedelta
from typing import Optional, Tuple

from fastapi import HTTPException
from sqlalchemy import func, or_, select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession

from fitness_management.models import Appointment, Coach, Course, Member, Schedule
from fitness_management.schemas.appointment import AppointmentCreate
from fitness_management.crud.course import get_booked_count
from fitness_management.crud.member import sync_card_statuses
from fitness_management.utils.status import ACTIVE_STATUSES, RESOLVABLE_STATUSES


async def get_appointment(db: AsyncSession, appointment_id: int) -> Optional[Appointment]:
    """按主键查询预约记录。"""
    return await db.scalar(select(Appointment).where(Appointment.id == appointment_id))


def _apply_quota(course: Optional[Course], delta: int) -> None:
    """调整课程已预约人数，delta 为正表示占用名额，为负表示释放名额。"""
    if course is None:
        return
    current = course.booked_count or 0
    course.booked_count = max(0, current + delta)


async def list_appointments(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 10,
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    date_: Optional[date_type] = None,
    member_id: Optional[int] = None,
) -> Tuple[list[dict], int]:
    """分页查询预约列表（含会员、课程、教练名称，以及同步自教练排课的信息）。

    传入 member_id 时只返回该会员的预约，会员角色由此实现数据隔离。

    排课信息（schedule_date / schedule_start / schedule_end / schedule_location /
    schedule_status）取自预约关联的 coach_schedule：优先按 appointment.schedule_id 直接取，
    schedule_id 为空时再按「同一课程 + 同一日期 + 同一时间」回退匹配当前排课
    （兼容历史预约与排课被重建的场景）。这样会员看到的课程时间/地点/状态与教练工作台一致。
    """
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
            Appointment.schedule_id,
            Schedule.schedule_date,
            Schedule.start_time.label("schedule_start"),
            Schedule.end_time.label("schedule_end"),
            Schedule.location.label("schedule_location"),
            Schedule.status.label("schedule_status"),
        )
        .join(Member, Member.id == Appointment.member_id)
        .join(Course, Course.id == Appointment.course_id)
        .outerjoin(Coach, Coach.id == Course.coach_id)
        .outerjoin(Schedule, Schedule.id == Appointment.schedule_id)
    )

    # 关键词：会员姓名 / 课程名称 / 教练姓名
    if keyword is not None and keyword.strip() != "":
        stmt = stmt.where(
            or_(
                Member.name.ilike(f"%{keyword}%"),
                Course.name.ilike(f"%{keyword}%"),
                Coach.name.ilike(f"%{keyword}%"),
            )
        )

    if member_id is not None:
        stmt = stmt.where(Appointment.member_id == member_id)
    if status:
        stmt = stmt.where(Appointment.status == status)
    if date_:
        # 用范围查询代替 DATE() 函数，命中 appointment_time 索引
        start = datetime.combine(date_, time_type.min)
        stmt = stmt.where(
            Appointment.appointment_time >= start,
            Appointment.appointment_time < start + timedelta(days=1),
        )

    # 总数
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    # 分页
    stmt = (
        stmt.order_by(Appointment.appointment_time.desc(), Appointment.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = (await db.execute(stmt)).mappings().all()
    items = [dict(row) for row in rows]

    # 回退：schedule_id 为空的预约，按 (课程, 日期, 时间) 匹配当前排课
    unlinked = [it for it in items if it.get("schedule_id") is None]
    if unlinked:
        candidates = [
            (it["course_id"], it["appointment_time"].date(), it["appointment_time"].time())
            for it in unlinked
            if it.get("appointment_time") is not None
        ]
        if candidates:
            sched_rows = (
                await db.execute(
                    select(
                        Schedule.id,
                        Schedule.course_id,
                        Schedule.schedule_date,
                        Schedule.start_time,
                        Schedule.end_time,
                        Schedule.location,
                        Schedule.status,
                    ).where(
                        tuple_(Schedule.course_id, Schedule.schedule_date, Schedule.start_time).in_(
                            candidates
                        )
                    )
                )
            ).mappings().all()
            by_key = {
                (r["course_id"], r["schedule_date"], r["start_time"]): r
                for r in sched_rows
            }
            for it in unlinked:
                appt_time = it.get("appointment_time")
                if appt_time is None:
                    continue
                key = (it["course_id"], appt_time.date(), appt_time.time())
                sch = by_key.get(key)
                if sch is not None:
                    it["schedule_id"] = sch["id"]
                    it["schedule_date"] = sch["schedule_date"]
                    it["schedule_start"] = sch["start_time"]
                    it["schedule_end"] = sch["end_time"]
                    it["schedule_location"] = sch["location"]
                    it["schedule_status"] = sch["status"]

    return items, total


async def create_appointment(
    db: AsyncSession,
    data: AppointmentCreate,
    member_id: Optional[int] = None,
) -> Tuple[Appointment, Member, Course]:
    """会员预约课程，返回 (预约记录, 会员, 课程)。"""
    final_member_id = member_id if member_id is not None else data.member_id

    # 会员必须存在且状态正常
    member = await db.scalar(select(Member).where(Member.id == final_member_id))
    if not member:
        raise HTTPException(status_code=404, detail="会员不存在")
    # 卡状态是 card_expire 的派生值，先按到期时间归正再判断：
    # 否则「卡早就过期、status 还写着正常」的会员照样能约上课。
    await sync_card_statuses(db, member_id=member.id)
    await db.refresh(member)
    if member.status != "正常":
        raise HTTPException(status_code=400, detail=f"会员卡状态为「{member.status}」，不能预约")

    # 课程必须存在且可预约
    course = await db.scalar(select(Course).where(Course.id == data.course_id))
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在")
    # 课程状态用黑名单，库里历史值「正常」也视为可预约
    if course.status in ("已下架", "已满员", "停课", "取消", "关闭"):
        raise HTTPException(status_code=400, detail=f"课程当前状态为「{course.status}」，不可预约")

    # 课程未满员，团课看 max_count，私教看 capacity。
    # 用实际占用名额数，不用 course.booked_count 那一列 —— 它是增删时 ±1 维护出来的
    # 派生值，历史数据里已经和真实预约数对不上（库里课程 2 写着 1，实际占着 7 个名额），
    # 拿它判满员会让已经满了的课继续放人进来。判重的口径与 member_center 的课表一致。
    capacity = course.max_count or course.capacity
    booked = await get_booked_count(db, course.id)
    if capacity and booked >= capacity:
        raise HTTPException(status_code=400, detail="课程已满员")

    # 同一会员同一时段不能重复预约
    duplicated = await db.scalar(
        select(func.count())
        .select_from(Appointment)
        .where(
            Appointment.member_id == final_member_id,
            Appointment.appointment_time == data.appointment_time,
            # 「待预约」是「已预约」的历史同义写法，必须一起判重，否则同一时段能重复下单
            Appointment.status.in_(ACTIVE_STATUSES),
        )
    )
    if duplicated:
        raise HTTPException(status_code=400, detail="同一时段已存在有效预约")

    appointment = Appointment(
        member_id=final_member_id,
        course_id=course.id,
        appointment_time=data.appointment_time,
        status="已预约",
        checked_in=False,
    )
    # 关联教练排课：按「同一课程 + 同一日期 + 同一时间」找到那一次课，
    # 会员预约视图即可同步排课的时间 / 地点 / 状态（教练改排课后也会跟着变）。
    linked = await db.scalar(
        select(Schedule).where(
            Schedule.course_id == course.id,
            Schedule.schedule_date == data.appointment_time.date(),
            Schedule.start_time == data.appointment_time.time(),
        )
    )
    if linked is not None:
        appointment.schedule_id = linked.id
    db.add(appointment)
    # 占用课程名额
    _apply_quota(course, 1)
    await db.flush()
    return appointment, member, course


async def cancel_appointment(
    db: AsyncSession,
    appointment_id: int,
    member_id: Optional[int] = None,
) -> Appointment:
    """取消预约并释放课程名额。"""
    appointment = await get_appointment(db, appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="预约不存在")

    # 会员只能取消本人的预约
    if member_id is not None and appointment.member_id != member_id:
        raise HTTPException(status_code=403, detail="只能取消本人的预约")

    if appointment.status == "已完成":
        raise HTTPException(status_code=400, detail="已完成的课程不能取消")
    if appointment.status == "已取消":
        raise HTTPException(status_code=400, detail="该预约已取消，请勿重复操作")

    appointment.status = "已取消"
    course = await db.scalar(select(Course).where(Course.id == appointment.course_id))
    _apply_quota(course, -1)
    await db.flush()
    return appointment


async def checkin_appointment(db: AsyncSession, appointment_id: int) -> Appointment:
    """预约签到。"""
    appointment = await get_appointment(db, appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="预约不存在")
    if appointment.status == "已取消":
        raise HTTPException(status_code=400, detail="已取消的预约不能签到")
    if appointment.status == "已完成":
        raise HTTPException(status_code=400, detail="该预约已完成，无需签到")

    appointment.status = "已签到"
    appointment.checked_in = True
    await db.flush()
    return appointment


async def resolve_appointment(
    db: AsyncSession,
    appointment_id: int,
    target_status: str,
    remark: Optional[str] = None,
) -> Appointment:
    """处理预约冲突：修正状态与备注，并同步课程名额。"""
    if target_status not in RESOLVABLE_STATUSES:
        raise HTTPException(
            status_code=400,
            detail="预约状态不合法，可选：" + "、".join(RESOLVABLE_STATUSES),
        )

    appointment = await get_appointment(db, appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="预约不存在")

    before_active = appointment.status in ACTIVE_STATUSES
    after_active = target_status in ACTIVE_STATUSES

    appointment.status = target_status
    if remark is not None:
        appointment.remark = remark
    if target_status == "已取消":
        appointment.checked_in = False

    # 状态在「占用名额 / 不占用名额」之间切换时同步课程已预约人数
    if before_active != after_active:
        course = await db.scalar(select(Course).where(Course.id == appointment.course_id))
        _apply_quota(course, 1 if after_active else -1)

    await db.flush()
    return appointment
