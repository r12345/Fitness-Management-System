"""教练工作台相关数据库操作。

教练身份由 API 层从当前登录用户解析后以 coach_id 传入，
本模块只负责数据读写与业务校验，不感知 HTTP 之外的请求细节。
"""
import datetime
from datetime import date as date_type
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import Select, and_, func, or_, select
from sqlalchemy import update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from fitness_management.models import (
    Appointment,
    CheckinRecord,
    Coach,
    Course,
    DictItem,
    Member,
    Schedule,
    TrainPlan,
)
from fitness_management.crud.member import sync_card_statuses
from fitness_management.schemas.coach_panel import MemberBrief, ScheduleUpdate
from fitness_management.utils.status import ACTIVE_STATUSES


# 排课状态的唯一权威是「排课时间」，status 只是它的派生值：
#   · 人工状态（已签到、已取消）优先保留——它们记录的是教练做过的动作
#   · 其余一律按当前时间判定：还没到点=未开始、已开课未下课=进行中、已过下课时间=已结束
SCHEDULE_PENDING = "未开始"
SCHEDULE_ONGOING = "进行中"
SCHEDULE_FINISHED = "已结束"
SCHEDULE_CHECKED_IN = "已签到"
SCHEDULE_CANCELLED = "已取消"

# 人工状态集合，同步时要跳过
MANUAL_SCHEDULE_STATUSES = frozenset({SCHEDULE_CHECKED_IN, SCHEDULE_CANCELLED})
# 允许人工设置的目标状态
SCHEDULE_SETTABLE_STATUSES = (SCHEDULE_PENDING, SCHEDULE_CHECKED_IN, SCHEDULE_CANCELLED)

# 库里混进过一批英文值（历史导入留下的）：cancel 就是已取消，
# normal/full 在当时没有明确语义（full 只是说预约满了），一律交给时间重新判定。
SCHEDULE_STATUS_ALIASES = {
    "cancel": SCHEDULE_CANCELLED,
    "cancelled": SCHEDULE_CANCELLED,
    "normal": None,
    "full": None,
}
# 冲突检测要排除的「已取消」写法（含历史值）
CANCELLED_STATUSES = (SCHEDULE_CANCELLED, "cancel", "cancelled")

# 签到的允许时间余量（分钟），作用在课程时段的两端。
# 0 = 严格「落在课程时段内」才能签到：没到点签不了、下课了也补不了。
# 现实里教练可能提前一两分钟点，确有需要只改这一个常量，不用动判断逻辑。
CHECKIN_GRACE_MINUTES = 0


def appointment_belongs_to_schedule(member_id: Optional[int] = None):
    """「这条预约属于这条排课」的条件。

    两种关联方式都算：
      · appointment.schedule_id 直接指向该排课（新建预约时写入的）；
      · schedule_id 为空但「同课程 + 同日期 + 同开始时间」对得上 ——
        库里早期导入的预约没有 schedule_id（30 条里 25 条），
        不兜底的话这些占用中的名额会被漏算。

    member_id 传入时再限定到某个会员，用来判断「我是不是已经约过这一节」。
    """
    same_slot = or_(
        Appointment.schedule_id == Schedule.id,
        and_(
            Appointment.schedule_id.is_(None),
            Appointment.course_id == Schedule.course_id,
            Appointment.appointment_time
            == func.timestamp(Schedule.schedule_date, Schedule.start_time),
        ),
    )
    if member_id is not None:
        return and_(Appointment.member_id == member_id, same_slot)
    return same_slot


async def sync_schedule_appointments(
    db: AsyncSession,
    schedule: Schedule,
    old_date: Optional[date_type],
    old_start: Optional[datetime.time],
) -> int:
    """排课改了日期 / 开始时间后，把挂在它名下的预约时间同步过去。

    ``appointment.appointment_time`` 是会员下单那一刻对排课时间的**快照**，
    不会自己跟着排课变。教练把这一次课挪到别的日子或时段之后，快照就停留在旧值：
    预约管理页、会员的「我的预约」、课程预约名单、会员详情里的预约记录全都还在显示旧时间，
    按日期筛选也筛不到（那里的过滤条件正是 appointment_time）。

    这里把快照矫正到排课的最新时间，并且一次性收口两种关联方式：

      · ``schedule_id`` 已经指向这条排课的；
      · ``schedule_id`` 为空、但「同课程 + 同旧日期 + 同旧开始时间」对得上的历史预约 ——
        顺手把 ``schedule_id`` 补上，否则这条预约下次改期又会跟丢。

    已取消 / 已完成的预约同样同步：它们记的是「同一次课的预约」，
    跟着排课走才对得上，新旧只体现在时间上；不同步会出现同一次课在
    「已预约」页显示新时间、在「已取消」页显示旧时间的自相矛盾。

    返回同步（或被收编）的预约条数。时间没实际变化时直接返回 0，不写库。
    """
    if old_date is None or old_start is None:
        return 0
    # 排课的新时间与「这条排课」的标识都要用；调用于改字段之后，
    # 所以 schedule 上已经是新值，旧值由调用方提前留好传进来。
    new_dt = datetime.datetime.combine(schedule.schedule_date, schedule.start_time)
    old_dt = datetime.datetime.combine(old_date, old_start)
    if new_dt == old_dt:
        return 0

    condition = or_(
        Appointment.schedule_id == schedule.id,
        and_(
            Appointment.schedule_id.is_(None),
            Appointment.course_id == schedule.course_id,
            Appointment.appointment_time == old_dt,
        ),
    )
    result = await db.execute(
        sa_update(Appointment)
        .where(condition)
        .values(appointment_time=new_dt, schedule_id=schedule.id)
        # 条件里用了 or_/is_ 这类表达式，交给 ORM 去「在 Python 里复算」容易踩空，
        # 直接关掉会话同步 —— 本次请求不会再用到这些 Appointment 对象。
        .execution_options(synchronize_session=False)
    )
    return int(result.rowcount or 0)


def booked_count_column(member_id: Optional[int] = None):
    """「这一节排课已约几人」的标量子查询（教练工作台用）。

    原来这里直接读 coach_schedule.booked_count，但那一列**只在造排课时写过 0**，
    之后没有任何地方维护 → 教练工作台的「已约人数」恒为 0 人。
    改成从预约表现算，与真实报名情况一致。

    只数仍占用名额的状态（已预约 / 待预约 / 已签到）；已取消、已完成已把名额还回来了。
    """
    return (
        select(func.count())
        .select_from(Appointment)
        .where(
            Appointment.status.in_(ACTIVE_STATUSES),
            appointment_belongs_to_schedule(member_id),
        )
        .correlate(Schedule)
        .scalar_subquery()
        .label("booked_count")
    )


def course_booked_count_column():
    """「这门课程累计已约几人」的标量子查询（会员预约列表用）。

    会员预约页上的「已约/上限」必须和后端放行/拒绝的口径一致 ——
    create_appointment 判满员用的是**整门课程**的占用数（capacity = max_count or capacity，
    数的是该课程名下所有占用中的预约），不是单节排课的。若这里按节数，
    就会出现「显示还有名额、点下去却被拒：课程已满员」的假按钮。
    """
    return (
        select(func.count())
        .select_from(Appointment)
        .where(
            Appointment.status.in_(ACTIVE_STATUSES),
            Appointment.course_id == Course.id,
        )
        .correlate(Course)
        .scalar_subquery()
        .label("booked_count")
    )


def calc_schedule_status(
    schedule_date,
    start_time,
    end_time,
    current: Optional[str] = None,
    now: Optional[datetime.datetime] = None,
) -> str:
    """按排课时间推导状态。人工状态（已签到/已取消）原样返回。"""
    mapped = SCHEDULE_STATUS_ALIASES.get(current, current) if isinstance(current, str) else current
    if mapped in MANUAL_SCHEDULE_STATUSES:
        return mapped
    if schedule_date is None or start_time is None or end_time is None:
        return mapped or SCHEDULE_PENDING
    now = now or datetime.datetime.now()
    start_dt = datetime.datetime.combine(schedule_date, start_time)
    end_dt = datetime.datetime.combine(schedule_date, end_time)
    if now >= end_dt:
        return SCHEDULE_FINISHED
    if now >= start_dt:
        return SCHEDULE_ONGOING
    return SCHEDULE_PENDING


def checkin_window(schedule, now: Optional[datetime.datetime] = None) -> tuple[datetime.datetime, datetime.datetime]:
    """该排课允许签到的时间窗（两端都含，再加 CHECKIN_GRACE_MINUTES 余量）。"""
    now = now or datetime.datetime.now()
    start_dt = datetime.datetime.combine(schedule.schedule_date, schedule.start_time)
    end_dt = datetime.datetime.combine(schedule.schedule_date, schedule.end_time)
    grace = datetime.timedelta(minutes=CHECKIN_GRACE_MINUTES)
    return start_dt - grace, end_dt + grace


def ensure_checkin_allowed(schedule, now: Optional[datetime.datetime] = None) -> None:
    """签到必须发生在课程时段内，否则抛 400。

    不按这一条卡住的话，「签到」会退化成一句谁都点得动的按钮：下个月的课能提前签、
    上周漏签的课也能跨周补签，签到记录就不再是「这节课他真的到了」的凭据。
    这里用后端时间判定 —— 前端按钮是个提示，能不能签由服务端说了算。

    与 calc_schedule_status 同源：状态是「进行中」的时刻，正是这里允许签到的时刻，
    所以前端只用「状态 == 进行中」来决定要不要显示签到按钮，两边不会打架。
    """
    if schedule.schedule_date is None or schedule.start_time is None or schedule.end_time is None:
        raise HTTPException(status_code=400, detail="排课时间不完整，无法签到")
    now = now or datetime.datetime.now()
    window_start, window_end = checkin_window(schedule, now)
    if now < window_start:
        raise HTTPException(
            status_code=400,
            detail=(
                f"课程还没开始：{schedule.schedule_date} "
                f"{schedule.start_time.strftime('%H:%M')} 起才能签到"
            ),
        )
    if now > window_end:
        raise HTTPException(
            status_code=400,
            detail=(
                f"课程已结束（{schedule.start_time.strftime('%H:%M')}~"
                f"{schedule.end_time.strftime('%H:%M')}），不能补签"
            ),
        )


async def sync_schedule_statuses(db: AsyncSession, coach_id: Optional[int] = None) -> int:
    """把排课状态按当前时间归正，返回修正条数（顺带把历史英文值中文化）。

    与会员卡状态一样，在读取排课前惰性调用：没人会记得去点「刷新状态」，
    放在查询前自动执行，教练看到的才始终是当前真实状态。
    """
    stmt = select(Schedule)
    if coach_id is not None:
        stmt = stmt.where(Schedule.coach_id == coach_id)
    rows = (await db.execute(stmt)).scalars().all()
    now = datetime.datetime.now()
    fixed = 0
    for schedule in rows:
        want = calc_schedule_status(
            schedule.schedule_date, schedule.start_time, schedule.end_time, schedule.status, now
        )
        if schedule.status != want:
            schedule.status = want
            fixed += 1
    if fixed:
        await db.commit()
    return fixed


# ============================ 排课窗口 ============================
# 排课由课程时间派生，本质上是一张无限重复的课表。教练工作台只看一个滑动窗口。
# 窗口是「从今天起往后 4 周」（用户定的口径：会员要看到当前时间之后四周、全部教练的排课；
# 只看过去两周没意义——已结束的课既不能改也不能签到）。生成与展示共用同一个窗口函数，
# 保证「显示出来的都生成过、生成出来的都在显示范围内」，两边不会各写一套天数。
SCHEDULE_WINDOW_WEEKS = 4

# 只有已上架的课程才继续往后派生排课；下架的课程不再新增排课。
ACTIVE_COURSE_STATUS = "已上架"


def schedule_window(today: Optional[date_type] = None) -> tuple[date_type, date_type]:
    """排课窗口：从今天起往后 4 周（端点包含在内）。

    返回 (起始日, 结束日)，起始日就是今天。过去日期不再派生、也不再展示。
    """
    base = today or date_type.today()
    return base, base + datetime.timedelta(weeks=SCHEDULE_WINDOW_WEEKS)


def _week_key(value: date_type) -> tuple[int, int]:
    """ISO (年, 周) 键，用来判断两条排课是否落在同一周。"""
    iso = value.isocalendar()
    return iso[0], iso[1]


def _iter_weekday_occurrences(
    window_start: date_type, window_end: date_type, weekday: int
):
    """窗口内所有落在指定星期几的日期。"""
    day = window_start + datetime.timedelta(days=(weekday - window_start.weekday()) % 7)
    while day <= window_end:
        yield day
        day += datetime.timedelta(days=7)


def _course_schedule_template(course) -> Optional[tuple["datetime.time", "datetime.time"]]:
    """课程 → (开始时间, 结束时间)。课程没填上课时间时返回 None。

    结束时间 = 开始时间 + 课程时长，这是「结束时间由课程时长来结束」的落点；
    跨零点也不做特殊处理（真实课表不会出现 20 小时的课，库里那条 505 分钟的
    异常时长只影响它自己，不阻断其它课程）。
    """
    if course.start_time is None:
        return None
    start = course.start_time.time()
    base = datetime.datetime.combine(date_type(2000, 1, 1), start)
    end = (base + datetime.timedelta(minutes=course.duration or 0)).time()
    return start, end


async def sync_course_schedules(
    db: AsyncSession,
    today: Optional[date_type] = None,
    course_ids: Optional[list[int]] = None,
    refresh: bool = False,
) -> int:
    """按课程把窗口内的排课补齐，返回新建条数。

    课程是权威，排课是它的派生值：
      · 星期几  ←  课程开始时间的星期几（「每周的这个时间」）
      · 开始时间 ←  课程开始时间的时分
      · 结束时间 ←  开始时间 + 课程时长
      · 上课地点 ←  课程的上课地点

    幂等键取 (课程, ISO 周) 而不是 (课程, 日期)：教练把某一次课挪到同一周的
    另一天之后，那一周依旧算「已排」，不会被重新生成一条回来。

    两种调用姿势，区别只在「已存在的排课碰不碰」：
      · refresh=False（读排课前、服务启动时）：只补缺失的周，已有的一律不动
        —— 教练改过的时间 / 地点必须留得住，否则每次打开页面都被打回课程原值。
      · refresh=True（课程的时间 / 时长 / 地点被改之后，传 course_ids 限定到该课程）：
        把该课程已有排课的「时间 / 时长 / 地点」校正为新值。
        日期仍然不碰：那是教练自己挪的，和课程时间无关。
    """
    window_start, window_end = schedule_window(today)

    stmt = select(Course).where(Course.start_time.isnot(None))
    if course_ids is not None:
        # 指定课程时不再看上下架状态：下架课程也要能把历史排课校正干净
        stmt = stmt.where(Course.id.in_(course_ids))
    else:
        stmt = stmt.where(Course.status == ACTIVE_COURSE_STATUS)
    courses = (await db.execute(stmt)).scalars().all()
    if not courses:
        return 0

    rows = (
        await db.execute(
            select(Schedule).where(
                Schedule.schedule_date >= window_start,
                Schedule.schedule_date <= window_end,
            )
        )
    ).scalars().all()
    # 每个课程、每一周只认一条：同周若有多条历史数据，以先读到的那条为准
    owned: dict[int, dict[tuple[int, int], Schedule]] = {}
    for row in rows:
        owned.setdefault(row.course_id, {}).setdefault(_week_key(row.schedule_date), row)

    created = 0
    touched = 0
    for course in courses:
        location = (course.location or "").strip()
        if not location:
            # 地点是排课的必填项。课程没填地点时不派生，避免造出一条没有地点的排课；
            # 课程表单会把地点作为必填项引导补上。
            continue
        template = _course_schedule_template(course)
        if template is None:
            continue
        start_time, end_time = template
        weekdays = owned.setdefault(course.id, {})

        for day in _iter_weekday_occurrences(window_start, window_end, course.start_time.weekday()):
            found = weekdays.get(_week_key(day))
            if found is None:
                schedule = Schedule(
                    coach_id=course.coach_id,
                    course_id=course.id,
                    schedule_date=day,
                    start_time=start_time,
                    end_time=end_time,
                    location=location,
                    booked_count=0,
                    status=SCHEDULE_PENDING,
                )
                schedule.status = calc_schedule_status(day, start_time, end_time, SCHEDULE_PENDING)
                db.add(schedule)
                weekdays[_week_key(day)] = schedule
                created += 1
                continue

            if not refresh:
                continue

            # 课程改了时间 / 时长 / 地点 → 这条已生成的排课跟着校正；日期不动
            if (found.start_time, found.end_time, found.location) != (start_time, end_time, location):
                old_start = found.start_time
                found.start_time = start_time
                found.end_time = end_time
                found.location = location
                found.status = calc_schedule_status(
                    found.schedule_date, start_time, end_time, found.status
                )
                # 开始时间变了，这条排课名下预约的快照也要跟着走。
                # 这里日期不动，所以「旧日期」就是排课当前日期。
                await sync_schedule_appointments(db, found, found.schedule_date, old_start)
                touched += 1

    if created or touched:
        await db.flush()
        await db.commit()
    return created


async def get_member_brief(db: AsyncSession, member_id: int) -> Optional[MemberBrief]:
    """按会员编号取简要信息（id + name）。

    编辑训练计划后要回填学员姓名，而创建该计划时用的会员对象不在会话里，
    异步环境下也不能靠 `plan.member` 懒加载，只能显式查一次。
    只选 id/name 两列，不用把整行捞出来。

    原先是 api/v1/coach_panel.py 里的私有函数 ``_member_brief``：
    它是一次数据库查询，属于 crud 的职责（合并在 schemas 里会让 schema 依赖 Session）。
    """
    row = (await db.execute(select(Member.id, Member.name).where(Member.id == member_id))).first()
    return MemberBrief(id=row[0], name=row[1]) if row else None


# 训练计划预设项：「基础选项 + 自由输入」的两个来源
# 「制定训练计划」的几个文本字段既要有基础选项（少打字、口径统一），
# 又必须允许教练自由输入（真实训练场景千变万化，不可能枚举完）。
# 前端用 <input list> + <datalist> 实现「下拉可选、也可手打」。
#
# 「主要部位」直接读 sys_dict 里 dict_type=body_part 的启用项——它是管理员可以在
# 系统设置里维护的字典，改字典就能改选项，不用发版。
# 其余四项（目标/动作/组数次数/频率）库里没有对应字典，先用这里的常量兜底；
# 以后若也进了 sys_dict，只要往 _DICT_BACKED_FIELDS 里加一条即可。
_DICT_BACKED_FIELDS = ("body_part",)

PLAN_PRESET_CONSTANTS: dict[str, list[str]] = {
    "goal": ["增肌", "减脂", "塑形", "提升力量", "改善体态", "提升耐力", "康复训练"],
    "actions": [
        "深蹲", "卧推", "硬拉", "引体向上", "俯卧撑", "哑铃飞鸟",
        "坐姿划船", "高位下拉", "腿举", "弓步蹲", "臀桥", "平板支撑",
        "站姿肩推", "二头弯举", "三头下压", "卷腹",
    ],
    "sets_reps": ["3 组 × 12 次", "4 组 × 10 次", "5 组 × 5 次", "3 组 × 15 次", "2 组 × 20 次", "每组力竭"],
    "frequency": ["每周 1 次", "每周 2 次", "每周 3 次", "每周 4 次", "每周 5 次", "每天"],
}


async def _dict_values(db: AsyncSession, dict_type: str) -> list[str]:
    """读 sys_dict 里某个类型下所有**启用**的字典值（按录入顺序）。

    去空、去重后返回；字典里一条都没有时返回空列表，由调用方决定兜底。
    管理员在「系统设置 - 字典配置」里改了字典，这里的选项跟着变，不用发版。
    """
    rows = (
        await db.execute(
            select(DictItem.dict_value)
            .where(DictItem.dict_type == dict_type, DictItem.status == "enable")
            .order_by(DictItem.id)
        )
    ).scalars().all()
    values = [str(r).strip() for r in rows if r and str(r).strip()]
    return list(dict.fromkeys(values))


async def list_plan_presets(db: AsyncSession) -> dict[str, list[str]]:
    """训练计划弹窗的预设候选值。

    body_part 走 sys_dict（管理员可维护），其余走常量；
    返回结构固定为 {字段名: [候选值...]}，前端直接用字段名取。
    """
    presets: dict[str, list[str]] = {k: list(v) for k, v in PLAN_PRESET_CONSTANTS.items()}

    for field in _DICT_BACKED_FIELDS:
        values = await _dict_values(db, field)
        # 字典里有值就用字典的；字典空了则保留常量兜底，别把选项删光
        if values:
            presets[field] = values

    return presets


async def list_assignable_members(
    db: AsyncSession, coach_id: int, keyword: Optional[str] = None
) -> list[dict]:
    """「新增学员」下拉框的数据源：可以从数据库里挑的会员，按姓名/手机号筛。

    只给两种人：
      · 还没有归属教练的会员（coach_id 为空）—— 新会员、散客都在这儿；
      · 已经归属自己的（coach_id = 我）—— 列表里能重复选中，不会因为
        「已经是我的人」而在下拉框里找不到。
    已经属于别的教练的不列出来：改派是前台/管理员的活，教练之间不该互相抢学员。

    keyword 按姓名或手机号模糊匹配 —— 会员多起来以后，
    下拉框只靠名字翻是很费劲的。
    """
    # 卡状态跟着到期时间走，下拉框上要显示状态，读之前先归正
    await sync_card_statuses(db)

    stmt = select(
        Member.id.label("member_id"),
        Member.name,
        Member.phone,
        Member.card_type,
        Member.card_expire,
        Member.status,
    ).where(or_(Member.coach_id.is_(None), Member.coach_id == coach_id))

    if keyword and keyword.strip():
        text = f"%{keyword.strip()}%"
        stmt = stmt.where(or_(Member.name.ilike(text), Member.phone.ilike(text)))

    rows = (await db.execute(stmt.order_by(Member.id.asc()).limit(200))).mappings().all()
    return [dict(row) for row in rows]


async def get_my_schedules(
    db: AsyncSession,
    coach_id: int,
    status: Optional[str] = None,
    schedule_date: Optional[date_type] = None,
) -> list[dict]:
    """查询指定教练的排课列表（含课程名称），支持按状态与日期筛选。

    只返回「今天前后各 2 周」窗口内的排课 —— 排课是按课程时间无限重复派生的，
    不设窗口的话列表会越滚越长，教练真正要看的无非是最近这一段。

    排序保持「日期倒序」：未来的课在最上面，往下翻是刚上完的。
    """
    window_start, window_end = schedule_window()

    # 先按课程把窗口内的排课补齐（新开的课、拖过的窗口都要能立刻看到），
    # 再按当前时间归正状态。顺序不能反：新生成的排课还没做过状态判定。
    await sync_course_schedules(db)
    # 归正状态要排在状态过滤之前：否则「早就上完了、状态还写着未开始」
    # 的排课既不会出现在「已结束」筛选里，又会混进「未开始」列表。
    await sync_schedule_statuses(db, coach_id)

    stmt: Select = (
        select(
            Schedule.id,
            Schedule.coach_id,
            Schedule.course_id,
            Course.name.label("course_name"),
            # 课程时长：改排课时用它按「结束时间 = 开始时间 + 时长」自动补结束时间
            Course.duration.label("duration"),
            Schedule.schedule_date,
            Schedule.start_time,
            Schedule.end_time,
            Schedule.location,
            booked_count_column(),
            Schedule.status,
        )
        .join(Course, Course.id == Schedule.course_id)
        .where(
            Schedule.coach_id == coach_id,
            Schedule.schedule_date >= window_start,
            Schedule.schedule_date <= window_end,
        )
    )
    if status:
        stmt = stmt.where(Schedule.status == status)
    if schedule_date:
        stmt = stmt.where(Schedule.schedule_date == schedule_date)

    stmt = stmt.order_by(Schedule.schedule_date.desc(), Schedule.start_time.asc())
    rows = (await db.execute(stmt)).mappings().all()
    return [dict(row) for row in rows]


async def list_upcoming_schedules(
    db: AsyncSession,
    course_type: Optional[str] = None,
    keyword: Optional[str] = None,
    member_id: Optional[int] = None,
) -> list[dict]:
    """查询窗口内**全部教练**的排课，给会员「预约课程」用。

    与 get_my_schedules 的三处差异：
    1. 不按教练过滤 —— 会员要看到馆里所有教练的课，不只是自己那个教练；
    2. 排序改日期正序 —— 会员关心「最近哪一节能约」，而不是「最近上过什么」；
    3. 带出课程容量并算出 can_book —— 前端据此判断按钮能不能点。

    can_book 的口径和后端真正的预约校验一致：排课状态为「未开始」且课程没约满。
    这里的 booked_count 数的是**整门课程**的占用数（不是单节排课的）——
    满员是课程级的约束，按节数会让按钮显示可约、点下去却被拒。

    course_type / keyword 对应预约页上的「公共团课 / 私教课程」分页与搜索框：
    排课本身只带 course_id，会员要按课程维度筛选就得在这里关联 Course 过滤，
    前端不在本地筛（分页与筛选口径都留在服务端一处）。

    member_id 传入时额外算出 booked_by_me（这一节我约过没有），
    会员端据此把按钮换成「已预约」，不用等后端报重复预约的错。
    """
    window_start, window_end = schedule_window()

    # 新开的课程、拖过的窗口都要立刻出现在会员眼前，查之前先补齐；
    # 状态同样要归正，否则「已到点还写着未开始」的课会被当成可预约。
    await sync_course_schedules(db)
    await sync_schedule_statuses(db)

    stmt = (
        select(
            Schedule.id.label("schedule_id"),
            Schedule.course_id,
            Schedule.coach_id,
            Course.name.label("course_name"),
            Course.course_type.label("course_type"),
            Course.category.label("category"),
            Coach.name.label("coach_name"),
            # 课程时长：前端改时间后按「结束 = 开始 + 时长」自动带出结束时间时用
            Course.duration.label("duration"),
            Schedule.schedule_date,
            Schedule.start_time,
            Schedule.end_time,
            Schedule.location,
            # 已约人数用「整门课程」的口径：与 create_appointment 判满员、
            # 以及管理端课程列表的「已约/上限」是同一个数，按钮不会说谎
            course_booked_count_column(),
            Schedule.status,
            Course.max_count,
            Course.capacity,
        )
        .join(Course, Course.id == Schedule.course_id)
        .outerjoin(Coach, Coach.id == Schedule.coach_id)
        .where(
            Schedule.schedule_date >= window_start,
            Schedule.schedule_date <= window_end,
        )
    )
    if course_type:
        stmt = stmt.where(Course.course_type == course_type)
    if keyword and keyword.strip():
        text = f"%{keyword.strip()}%"
        stmt = stmt.where(or_(Course.name.ilike(text), Coach.name.ilike(text)))
    if member_id is not None:
        # 「我约过这一节没有」：约过就不该再显示预约按钮，
        # 否则会员点下去只会收到「同一时段已存在有效预约」这条后端报错。
        stmt = stmt.add_columns(
            booked_count_column(member_id).label("my_booked_count")
        )

    rows = (await db.execute(
        stmt.order_by(Schedule.schedule_date.asc(), Schedule.start_time.asc())
    )).mappings().all()

    items = []
    for row in rows:
        item = dict(row)
        # 团课看 max_count，私教看 capacity，和 create_appointment 里的判断保持一致
        capacity = item.get("max_count") or item.get("capacity")
        booked = item.get("booked_count") or 0
        item["can_book"] = item.get("status") == "未开始" and (not capacity or booked < capacity)
        # 已经约过这一节的，直接告诉前端「已预约」，按钮换成不可点
        item["booked_by_me"] = bool(item.pop("my_booked_count", 0))
        items.append(item)
    return items


async def _has_schedule_conflict(
    db: AsyncSession,
    coach_id: int,
    data: ScheduleUpdate,
    exclude_id: Optional[int] = None,
) -> bool:
    """同一教练、同一日期是否存在时段重叠的未取消排课。

    exclude_id 用于「修改排课」：这条记录自己不该算冲突对象，
    否则把 14:00 的课挪到 14:30，会被自己的旧时段拦下来。
    """
    stmt = (
        select(func.count())
        .select_from(Schedule)
        .where(
            Schedule.coach_id == coach_id,
            Schedule.schedule_date == data.schedule_date,
            # 历史数据里「已取消」还写成过 cancel，两种都要排除，否则冲突检测会把
            # 已经取消掉的时段当成占用
            Schedule.status.notin_(CANCELLED_STATUSES),
            # 两个左闭右开区间重叠的充要条件
            Schedule.start_time < data.end_time,
            Schedule.end_time > data.start_time,
        )
    )
    if exclude_id is not None:
        stmt = stmt.where(Schedule.id != exclude_id)
    return bool(await db.scalar(stmt))


async def update_my_schedule(
    db: AsyncSession, schedule_id: int, coach_id: int, data: ScheduleUpdate
) -> Schedule:
    """修改自己名下的排课：日期、开始时间、结束时间、地点都能改。

    排课改由课程时间派生之后，就没有「手工新增」这回事了 ——
    课程一建，窗口内的排课自动排好；教练要动的是「这一次课挪到哪天、几点、在哪上」。
    课程归属进不来（排课挂在哪门课由课程表决定），状态也不在这里改。

    返回 ``(排课, 同步的预约条数)``：这一次课挪了时间，名下的预约快照
    （``appointment_time``）必须一起挪，条数由调用方转达给教练。
    """
    schedule = await db.scalar(
        select(Schedule).where(Schedule.id == schedule_id, Schedule.coach_id == coach_id)
    )
    if not schedule:
        raise HTTPException(status_code=404, detail="排课不存在")
    # 已取消的排课是一次明确的「这次不上了」，改时间会把取消意图盖掉；
    # 要恢复就先点「恢复正常」（状态接口把目标态设回未开始）
    if schedule.status in CANCELLED_STATUSES:
        raise HTTPException(status_code=400, detail="已取消的排课不能修改，请先恢复为未开始")
    if data.end_time <= data.start_time:
        raise HTTPException(status_code=400, detail="结束时间必须晚于开始时间")
    if await _has_schedule_conflict(db, coach_id, data, exclude_id=schedule_id):
        raise HTTPException(status_code=400, detail="教练排班冲突：该时段已有排课")

    # 预约是按「旧日期 + 旧开始时间」记下来的，改字段前先把旧值留一份
    old_date, old_start = schedule.schedule_date, schedule.start_time

    schedule.schedule_date = data.schedule_date
    schedule.start_time = data.start_time
    schedule.end_time = data.end_time
    schedule.location = data.location
    # 时段整个变了，此前那条「已签到」已经不再描述这一次课，
    # 所以不保留人工状态，统一按新时段重新判定。
    schedule.status = calc_schedule_status(data.schedule_date, data.start_time, data.end_time)
    await db.flush()
    # 排课已排好的预约跟着挪时间：否则预约管理 / 会员的预约课程还显示旧时间
    synced = await sync_schedule_appointments(db, schedule, old_date, old_start)
    return schedule, synced


async def update_my_schedule_status(
    db: AsyncSession, schedule_id: int, coach_id: int, target_status: str
) -> Schedule:
    """修改自己名下排课的状态（如签到确认）。"""
    if target_status not in SCHEDULE_SETTABLE_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"排课状态不合法，可选：{'、'.join(SCHEDULE_SETTABLE_STATUSES)}",
        )

    schedule = await db.scalar(
        select(Schedule).where(Schedule.id == schedule_id, Schedule.coach_id == coach_id)
    )
    if not schedule:
        raise HTTPException(status_code=404, detail="排课不存在")

    # 签到只在课程时段内有效。状态归正是「到点自动变进行中」，而签到是教练的动作，
    # 人工动作也得有时间边界 —— 否则这节课没上也能签，记录就不可信了。
    if target_status == SCHEDULE_CHECKED_IN:
        ensure_checkin_allowed(schedule)

    # 「已签到/已取消」是教练的动作，按目标状态落库；其余交给时间判定
    # （例如对一节早就上完的课「撤销签到」，结果应是「已结束」而不是「未开始」）
    schedule.status = calc_schedule_status(
        schedule.schedule_date, schedule.start_time, schedule.end_time, target_status
    )
    await db.flush()
    return schedule


async def get_my_students(db: AsyncSession, coach_id: int) -> list[dict]:
    """查询指定教练的学员列表。

    学员 = **归属这位教练的会员**（``member.coach_id``）**或**在他名下有过训练计划的会员。

    以前只认后者，于是「教练刚拉来、还没建计划的学员」永远进不了列表，
    也就没法给他建第一个计划 —— 先有鸡还是先有蛋。归属列补上这个缺口。
    每人取最新的训练计划，并带出最近一次到店打卡日期。
    """
    # 卡状态跟着到期时间走：学员列表要显示卡状态，读之前先归正，免得显示旧值
    await sync_card_statuses(db)

    # 每个学员在该教练名下的最新训练计划
    last_plan = (
        select(TrainPlan.member_id, func.max(TrainPlan.id).label("plan_id"))
        .where(TrainPlan.coach_id == coach_id)
        .group_by(TrainPlan.member_id)
        .subquery()
    )
    # 每个学员最近一次到店打卡日期
    last_checkin = (
        select(
            CheckinRecord.member_id,
            func.max(CheckinRecord.checkin_date).label("recent_training"),
        )
        .group_by(CheckinRecord.member_id)
        .subquery()
    )

    plan = aliased(TrainPlan)
    stmt = (
        select(
            Member.id.label("member_id"),
            Member.name,
            Member.phone,
            Member.gender,
            Member.age,
            Member.card_type,
            Member.card_expire,
            Member.status,
            plan.goal,
            plan.body_part.label("current_plan"),
            last_checkin.c.recent_training,
        )
        # 计划是「可有可无」的：归属这位教练的学员（刚拉来还没计划）也要出现在列表里
        .outerjoin(last_plan, last_plan.c.member_id == Member.id)
        .outerjoin(plan, plan.id == last_plan.c.plan_id)
        .outerjoin(last_checkin, last_checkin.c.member_id == Member.id)
        .where(or_(Member.coach_id == coach_id, last_plan.c.member_id.isnot(None)))
        .order_by(Member.id.asc())
    )
    rows = (await db.execute(stmt)).mappings().all()
    return [dict(row) for row in rows]


async def get_my_records(db: AsyncSession, coach: Coach) -> list[dict]:
    """查询指定教练的授课记录。

    coach 直接传入 ORM 对象，取其 score 作为每条记录的评分，
    避免 API 层已经查过的教练档案再查一次。comment 取自预约记录上的处理备注，
    当前数据模型没有独立的课程评价表，暂无更细粒度的评分来源。
    """
    score = round(float(coach.score), 1) if coach.score is not None else None

    stmt = (
        select(
            func.date(Appointment.appointment_time).label("date"),
            Course.name.label("course"),
            Member.name.label("student"),
            Course.duration.label("duration"),
            Appointment.remark,
        )
        .join(Course, Course.id == Appointment.course_id)
        .join(Member, Member.id == Appointment.member_id)
        .where(
            Course.coach_id == coach.id,
            Appointment.status.in_(("已签到", "已完成")),
        )
        .order_by(Appointment.appointment_time.desc())
    )
    rows = (await db.execute(stmt)).mappings().all()
    return [
        {
            "date": row["date"],
            "course": row["course"],
            "student": row["student"],
            "hours": round((row["duration"] or 0) / 60, 1),
            "score": score,
            "comment": row["remark"],
        }
        for row in rows
    ]
