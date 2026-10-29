"""预约相关数据库操作。"""
from datetime import date as date_type
from datetime import datetime, time as time_type, timedelta
from typing import Optional, Tuple

from fastapi import HTTPException
from sqlalchemy import func, or_, select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession

from fitness_management.models import Appointment, Coach, ConsumeRecord, Course, Member, Schedule
from fitness_management.schemas.appointment import AppointmentCreate
from fitness_management.crud.course import get_booked_count
from fitness_management.crud.member import sync_card_statuses
from fitness_management.utils.status import (
    ACTIVE_STATUSES,
    BOOKED,
    CANCELED,
    CHECKED_IN,
    CONFLICT_CHECK_STATUSES,
    FINISHED,
    PENDING,
    RESOLVE_SOURCE_STATUS,
    RESOLVE_TARGET_STATUSES,
    UNCHECKED_STATUSES,
)

# 会员对这条预约「什么都不能做」的排课状态：课已经上完/已经签过到了
MEMBER_BLOCKED_SCHEDULE_STATUSES = ("已结束", "已签到", "已取消")


async def get_appointment(db: AsyncSession, appointment_id: int) -> Optional[Appointment]:
    """按主键查询预约记录。"""
    return await db.scalar(select(Appointment).where(Appointment.id == appointment_id))


def _apply_quota(course: Optional[Course], delta: int) -> None:
    """调整课程已预约人数，delta 为正表示占用名额，为负表示释放名额。"""
    if course is None:
        return
    current = course.booked_count or 0
    course.booked_count = max(0, current + delta)


def _class_window(
    appointment: Appointment,
    course: Optional[Course] = None,
    schedule: Optional[Schedule] = None,
) -> Tuple[datetime, datetime]:
    """这条预约的上课时段 (开始, 结束)。

    优先用关联排课的日期与时段 —— 教练把这次课挪过之后，这里就是挪后的时间；
    预约没关联排课（历史数据）才按「预约时间 + 课程时长」推。
    """
    duration = (course.duration if course else None) or 0
    if (
        schedule is not None
        and schedule.schedule_date is not None
        and schedule.start_time is not None
    ):
        start = datetime.combine(schedule.schedule_date, schedule.start_time)
        if schedule.end_time is not None:
            end = datetime.combine(schedule.schedule_date, schedule.end_time)
        else:
            end = start + timedelta(minutes=duration)
    else:
        start = appointment.appointment_time
        end = start + timedelta(minutes=duration)
    if end <= start:
        end = start + timedelta(minutes=duration or 60)
    return start, end


def _window_of_row(row: dict) -> Tuple[Optional[datetime], Optional[datetime]]:
    """列表里一行的上课时段（排课优先，其次预约时间 + 课程时长）。"""
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    if row.get("schedule_date") and row.get("schedule_start"):
        start = datetime.combine(row["schedule_date"], row["schedule_start"])
        if row.get("schedule_end"):
            end = datetime.combine(row["schedule_date"], row["schedule_end"])
    if start is None and row.get("appointment_time"):
        start = row["appointment_time"]
    if start is not None and end is None:
        end = start + timedelta(minutes=row.get("course_duration") or 0)
    return start, end


def _row_action_flags(row: dict, now: Optional[datetime] = None) -> Tuple[bool, bool]:
    """这一行此刻「能不能签到 / 能不能取消」，由服务端算好给前端。

    为什么不让前端自己判：时间窗、排课状态都是服务端的口径，前端各算一份
    迟早对不上，而且失败方式是「按钮点了才报错」。这里算好下发，
    前端只负责决定要不要画这个按钮。

      · 签到：只有「已预约」且此刻正落在上课时段内 —— 早了没开始、晚了课已结束；
      · 取消：还没签到、且这节课没上完也没签过到（排课状态已结束/已签到就是不能动）。
    """
    now = now or datetime.now()
    start, end = _window_of_row(row)
    status = row.get("status")

    in_class = start is not None and end is not None and start <= now <= end
    can_checkin = status == BOOKED and in_class

    finished = (end is not None and now > end) or (
        row.get("schedule_status") in MEMBER_BLOCKED_SCHEDULE_STATUSES
    )
    can_cancel = status in UNCHECKED_STATUSES and not finished and status != CANCELED
    return can_checkin, can_cancel


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
            Course.duration.label("course_duration"),
            Course.price.label("course_price"),
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

    for it in items:
        it["can_checkin"], it["can_cancel"] = _row_action_flags(it)
    return items, total


async def _member_slot_conflict(
    db: AsyncSession, member_id: int, start: datetime, duration: int
) -> bool:
    """这个会员在 [start, start+duration) 这个时段里是不是已经有课了。

    比的是**区间重叠**而不是时间点相等：8:00 的团课和 8:30 的私教时间点不同，
    但会员不可能同时上两节。时长最短按 1 分钟算，免得两节 0 时长的课判不出重叠。
    """
    new_end = start + timedelta(minutes=max(int(duration or 0), 1))
    rows = (
        await db.execute(
            select(Appointment.appointment_time, Course.duration)
            .join(Course, Course.id == Appointment.course_id)
            .where(
                Appointment.member_id == member_id,
                Appointment.status.in_(CONFLICT_CHECK_STATUSES),
            )
        )
    ).all()
    for exist_start, exist_duration in rows:
        if exist_start is None:
            continue
        exist_end = exist_start + timedelta(minutes=max(int(exist_duration or 0), 1))
        if exist_start < new_end and exist_end > start:
            return True
    return False


async def create_appointment(
    db: AsyncSession,
    data: AppointmentCreate,
    member_id: Optional[int] = None,
) -> Tuple[Appointment, Member, Course]:
    """会员预约课程，返回 (预约记录, 会员, 课程)。

    时段撞车不再直接拒绝：会员在他已经有课的时段里再约一门，照样下单，
    但状态落成「待预约」（不占名额、不能签到），等前台在「处理冲突」里决定
    是转成「已预约」还是「已取消」。直接 400 的话会员连下单的机会都没有，
    前台也就看不到「这个人想上两节课」这件事。
    """
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

    # 同一会员同一时段：撞车就落成「待预约」，不撞车才是正常的「已预约」
    conflicted = await _member_slot_conflict(
        db, final_member_id, data.appointment_time, course.duration
    )

    appointment = Appointment(
        member_id=final_member_id,
        course_id=course.id,
        appointment_time=data.appointment_time,
        status=PENDING if conflicted else BOOKED,
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
    # 占用课程名额：「待预约」是冲突待处理，还没占到席位，先不 +1
    if not conflicted:
        _apply_quota(course, 1)
    await db.flush()
    return appointment, member, course


async def cancel_appointment(
    db: AsyncSession,
    appointment_id: int,
    member_id: Optional[int] = None,
) -> Appointment:
    """取消预约并释放课程名额。

    会员自己取消时多一道闸：课已经上完（排课状态已结束）或者已经签过到的，
    不能再退 —— 那是已经发生过的事，退掉只会让名额和消费记录对不上。
    前台/管理员取消属于纠错，不受这条限制。
    """
    appointment = await get_appointment(db, appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="预约不存在")

    # 会员只能取消本人的预约
    if member_id is not None and appointment.member_id != member_id:
        raise HTTPException(status_code=403, detail="只能取消本人的预约")

    if appointment.status == FINISHED:
        raise HTTPException(status_code=400, detail="已完成的课程不能取消")
    if appointment.status == CANCELED:
        raise HTTPException(status_code=400, detail="该预约已取消，请勿重复操作")

    if member_id is not None:
        schedule = (
            await db.scalar(select(Schedule).where(Schedule.id == appointment.schedule_id))
            if appointment.schedule_id
            else None
        )
        if schedule is not None and schedule.status in MEMBER_BLOCKED_SCHEDULE_STATUSES:
            raise HTTPException(
                status_code=400,
                detail=f"该次课已是「{schedule.status}」状态，不能取消，如有疑问请联系前台",
            )

    appointment.status = CANCELED
    course = await db.scalar(select(Course).where(Course.id == appointment.course_id))
    _apply_quota(course, -1)
    await db.flush()
    return appointment


async def _charge_course_fee(
    db: AsyncSession,
    member: Member,
    course: Optional[Course],
    operator: str,
) -> float:
    """按课程**当前**的课时费从会员余额里扣钱，并写一条消费记录，返回实扣金额。

    课时费取的是「签到这一刻」的 ``course.price`` —— 课程调过价就按新价算，
    预约下单时是多少钱不作数（会员端「可预约课程」显示的价格也是这个口径）。

    价格为 0 或没标价时不扣钱也不写流水：那种课本来就免费，
    硬写一条 0 元的消费记录只会把会员的消费明细弄脏。
    余额不够直接 400 —— 让会员欠着上课，账就永远对不上了。
    """
    charged = round(float(course.price or 0), 2) if course else 0.0
    if charged <= 0:
        return 0.0

    balance = float(member.balance or 0)
    if balance < charged:
        raise HTTPException(
            status_code=400,
            detail=(
                f"账户余额不足：本节课 {charged:.2f} 元，"
                f"当前余额 {balance:.2f} 元，请先充值"
            ),
        )
    member.balance = round(balance - charged, 2)
    db.add(
        ConsumeRecord(
            member_id=member.id,
            item=f"{course.name} 课时费",
            amount=charged,
            pay_method="余额扣款",
            operator=operator,
            created_at=datetime.now(),
        )
    )
    return charged


async def checkin_appointment(
    db: AsyncSession,
    appointment_id: int,
    member_id: Optional[int] = None,
    operator: Optional[str] = None,
) -> Tuple[Appointment, float, float]:
    """预约签到，返回 (预约记录, 本次扣款, 剩余余额)。

    只要这条预约的状态落到「已签到」，就按课程当前的课时费从会员余额里扣钱 ——
    **不管是会员本人签到还是前台/教练/管理员代签**。钱是会员上的这节课产生的，
    代签只是帮他点了确认，不能因为操作人不同就不扣（那等于会员随便找个人代签就免费上课）。

    ``member_id`` 传入表示会员本人自助签到，这时多一道闸：只在上课时段内放行 ——
    下个月的课提前签、上周漏签这周补签都不算数，签到记录要能证明「这节课他真的到了」。
    代签是管理动作，不受时间窗限制（补签、纠错都要能操作）。

    重复签到会被拦在状态校验上，不会重复扣钱。
    """
    appointment = await get_appointment(db, appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="预约不存在")

    # 会员只能给本人的预约签到
    if member_id is not None and appointment.member_id != member_id:
        raise HTTPException(status_code=403, detail="只能给本人的预约签到")

    if appointment.status == CANCELED:
        raise HTTPException(status_code=400, detail="已取消的预约不能签到")
    if appointment.status == CHECKED_IN or appointment.status == FINISHED:
        raise HTTPException(status_code=400, detail="该预约已签到，无需重复操作")
    if appointment.status == PENDING:
        # 冲突还没处理，这一单连名额都没占到，签到会让「已约人数」凭空多一个人
        raise HTTPException(
            status_code=400, detail="该预约存在时段冲突，请先在「处理冲突」里确认后再签到"
        )

    course = await db.scalar(select(Course).where(Course.id == appointment.course_id))
    member = await db.scalar(select(Member).where(Member.id == appointment.member_id))
    if not member:
        raise HTTPException(status_code=404, detail="该预约关联的会员不存在")
    schedule = (
        await db.scalar(select(Schedule).where(Schedule.id == appointment.schedule_id))
        if appointment.schedule_id
        else None
    )

    if member_id is not None:
        start, end = _class_window(appointment, course, schedule)
        now = datetime.now()
        if now < start:
            raise HTTPException(
                status_code=400,
                detail=f"课程还没开始：{start.strftime('%Y-%m-%d %H:%M')} 起才能签到",
            )
        if now > end:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"课程已结束（{start.strftime('%H:%M')}~{end.strftime('%H:%M')}），"
                    "不能补签，如有疑问请联系前台"
                ),
            )

    # 状态一变成「已签到」就按当前课时费扣款，代签也一样扣
    charged = await _charge_course_fee(db, member, course, operator or member.name)

    appointment.status = CHECKED_IN
    appointment.checked_in = True
    await db.flush()
    return appointment, charged, float(member.balance or 0)


async def resolve_appointment(
    db: AsyncSession,
    appointment_id: int,
    target_status: str,
    remark: Optional[str] = None,
) -> Appointment:
    """处理预约冲突：把「待预约」定成最终状态，并同步课程名额。

    只有「待预约」能走这个接口 —— 它是时段撞车留下的待办，需要前台拍板。
    其余状态（已预约/已签到/已完成/已取消）都是已经定了的事，
    再给一个「处理冲突」入口只会让人误以为它们还有问题。
    """
    if target_status not in RESOLVE_TARGET_STATUSES:
        raise HTTPException(
            status_code=400,
            detail="预约状态不合法，可选：" + "、".join(RESOLVE_TARGET_STATUSES),
        )

    appointment = await get_appointment(db, appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="预约不存在")
    if appointment.status != RESOLVE_SOURCE_STATUS:
        raise HTTPException(
            status_code=400,
            detail=f"只有「{RESOLVE_SOURCE_STATUS}」的预约需要处理冲突，当前为「{appointment.status}」",
        )

    before_active = appointment.status in ACTIVE_STATUSES
    after_active = target_status in ACTIVE_STATUSES

    # 转成占用名额的状态前先过一遍满员校验，别让「处理冲突」变成超卖的后门
    if after_active and not before_active:
        course = await db.scalar(select(Course).where(Course.id == appointment.course_id))
        capacity = course.max_count or course.capacity
        booked = await get_booked_count(db, course.id)
        if capacity and booked >= capacity:
            raise HTTPException(status_code=400, detail="课程已满员，无法转为「已预约」")

    appointment.status = target_status
    if remark is not None:
        appointment.remark = remark
    if target_status == CANCELED:
        appointment.checked_in = False

    # 状态在「占用名额 / 不占用名额」之间切换时同步课程已预约人数
    if before_active != after_active:
        course = await db.scalar(select(Course).where(Course.id == appointment.course_id))
        _apply_quota(course, 1 if after_active else -1)

    await db.flush()
    return appointment
