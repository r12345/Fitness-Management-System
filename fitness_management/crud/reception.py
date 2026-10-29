"""前台运营工作台相关数据库操作。"""
from datetime import date, datetime, time, timedelta
from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from fitness_management.crud.user import open_login_account
from fitness_management.models import (
    Member, Appointment, ConsumeRecord, Course, Equipment, Repair, Reception, User,
)
from fitness_management.schemas.reception import ReceptionCreate
from fitness_management.utils.status import UNRESOLVED_STATUSES, PENDING, CHECKED_IN, FINISHED, CANCELED


async def get_sum(db: AsyncSession):
    # 今日零点
    today_start = datetime.combine(date.today(), time.min)

    # 1. 今日新增会员
    q1 = select(func.count(Member.id)).where(Member.card_start >= today_start)
    today_new_members = (await db.execute(q1)).scalar_one() or 0

    # 2. 待处理预约：还没结课的预约。「待预约」= 时段冲突等前台处理，同样算待办
    q2 = select(func.count(Appointment.id)).where(Appointment.status.in_(UNRESOLVED_STATUSES))
    pending_appointments = (await db.execute(q2)).scalar_one() or 0

    # 3. 待报修器材：看器材当前状态，而不是报修流水条数。
    #    原来是 count(Repair.id)，把已经修好的历史报修单也算进来了，数字只增不减。
    q3 = select(func.count(Equipment.id)).where(Equipment.status == "维修")
    pending_repairs = (await db.execute(q3)).scalar_one() or 0

    # 4. 今日营收
    q4 = select(func.sum(ConsumeRecord.amount)).where(ConsumeRecord.created_at >= today_start)
    today_revenue = (await db.execute(q4)).scalar_one() or 0.00

    return {
        "today_new_members": today_new_members,
        "pending_appointments": pending_appointments,
        "pending_repairs": pending_repairs,
        "today_revenue": round(today_revenue,2)
    }


async def get_re_business_log(db: AsyncSession):
    """今日业务动态：把今天馆里发生的事按时间倒序排成一条流水。

    原来只查 consumption_record —— 今天没人消费，整块面板就是一片空白，
    看着像是功能坏了。可「业务动态」要回答的是「今天发生了什么」：
    有人开卡、有人约课、有人来上课签到、有人消费、有器材报修，这些都是动态。
    所以这里按来源分别取今天的数据，再合成一条时间线。

    各来源能拿到的时间精度不一样：消费有 created_at（精确到秒），预约有
    appointment_time，开卡只有 card_start 这个日期 —— 拿不到时分的
    时间列显示「—」，排序时归到当天起点，不会带着一个假时间混进流水里。
    """
    today = date.today()
    day_start = datetime.combine(today, time.min)
    day_end = day_start + timedelta(days=1)

    events: list[dict] = []

    # 1. 今日开卡：card_start 是日期，没有时分
    new_members = (
        await db.execute(
            select(Member.name, Member.card_type, Member.phone)
            .where(Member.card_start == today)
        )
    ).all()
    for name, card_type, _phone in new_members:
        events.append({
            "_sort": day_start,
            "time": "—",
            "operator": "前台",
            "target": name or "—",
            "content": f"办理{card_type or '会员卡'}开卡",
            "pay_method": "—",
        })

    # 2. 今日的预约与上课签到：同一条预约，签没签到说的是两件事
    appt_rows = (
        await db.execute(
            select(
                Appointment.appointment_time,
                Appointment.status,
                Member.name.label("member_name"),
                Course.name.label("course_name"),
            )
            .join(Member, Member.id == Appointment.member_id)
            .join(Course, Course.id == Appointment.course_id)
            .where(
                Appointment.appointment_time >= day_start,
                Appointment.appointment_time < day_end,
            )
        )
    ).all()
    for at, status, member_name, course_name in appt_rows:
        if status == CHECKED_IN or status == FINISHED:
            content = f"{course_name} 已签到上课"
            operator = "系统"
        elif status == CANCELED:
            content = f"{course_name} 预约已取消"
            operator = member_name or "—"
        elif status == PENDING:
            content = f"预约 {course_name}（时段冲突，待前台处理）"
            operator = member_name or "—"
        else:
            content = f"预约 {course_name}"
            operator = member_name or "—"
        events.append({
            "_sort": at or day_start,
            "time": at.strftime("%H:%M") if at else "—",
            "operator": operator,
            "target": member_name or "—",
            "content": content,
            "pay_method": "—",
        })

    # 3. 今日消费
    record_list = (
        await db.execute(
            select(ConsumeRecord)
            .options(joinedload(ConsumeRecord.member))
            .where(
                ConsumeRecord.created_at >= day_start,
                ConsumeRecord.created_at < day_end,
            )
        )
    ).scalars().all()
    for rec in record_list:
        events.append({
            "_sort": rec.created_at or day_start,
            "time": rec.created_at.strftime("%H:%M") if rec.created_at else "—",
            "operator": rec.operator or "—",
            "target": rec.member.name if rec.member else "—",
            "content": f"{rec.item or '消费'}，金额 {rec.amount if rec.amount is not None else ''} 元",
            "pay_method": rec.pay_method or "—",
        })

    # 4. 今日报修
    repair_rows = (
        await db.execute(
            select(Repair.repair_time, Repair.description, Equipment.name)
            .join(Equipment, Equipment.id == Repair.equipment_id)
            .where(
                Repair.repair_time >= day_start,
                Repair.repair_time < day_end,
            )
        )
    ).all()
    for rt, description, equipment_name in repair_rows:
        events.append({
            "_sort": rt or day_start,
            "time": rt.strftime("%H:%M") if rt else "—",
            "operator": "系统",
            "target": equipment_name or "—",
            "content": f"器材报修：{description or '—'}",
            "pay_method": "—",
        })

    events.sort(key=lambda e: e["_sort"], reverse=True)
    for e in events:
        e.pop("_sort", None)
    return {"items": events}


# 运营（前台）人员：管理员维护，列表 + 新增 + 删除。
# 账号与档案一起建、一起删，见 crud/user.open_login_account

async def list_staff(db: AsyncSession) -> list[dict]:
    """运营人员列表 = 「登录账号」∪ 「人员档案」。

    为什么不能只读 reception 表：能不能登进前台工作台，才是「是不是运营人员」
    的实质，档案表只补充薪资、入职时间这些信息。历史上有过一批人只注册了账号
    没建档案（老注册流程的 reception 分支漏了写档案），只读档案表的话，
    这些人在超管页面上会凭空消失 —— 明明能登录、却没人管得到。
    所以两边都列：有账号没档案的标 has_profile=false，有档案没账号的标 has_account=false。

    有档案的行沿用档案编号（id）作主键；只有账号的行没有档案编号，
    接口层删除要用 user_id 走 /staff/account/{user_id}。
    """
    accounts = (
        await db.execute(select(User).where(User.role == "reception").order_by(User.id.asc()))
    ).scalars().all()
    profiles = (
        await db.execute(select(Reception).order_by(Reception.id.asc()))
    ).scalars().all()

    accounts_by_id = {account.id: account for account in accounts}
    matched_account_ids: set[int] = set()
    items: list[dict] = []

    for profile in profiles:
        account = accounts_by_id.get(profile.user_id) if profile.user_id else None
        if account:
            matched_account_ids.add(account.id)
        items.append({
            "id": profile.id,
            "user_id": account.id if account else None,
            "username": account.username if account else None,
            "name": profile.name,
            "phone": profile.phone,
            "salary": profile.salary,
            "hire_date": profile.hire_date,
            "status": profile.status,
            "remark": profile.remark,
            "has_account": account is not None,
            "has_profile": True,
        })

    for account in accounts:
        if account.id in matched_account_ids:
            continue
        items.append({
            "id": None,
            "user_id": account.id,
            "username": account.username,
            "name": account.name or account.username,
            "phone": account.phone,
            "salary": None,
            "hire_date": None,
            "status": None,
            "remark": None,
            "has_account": True,
            "has_profile": False,
        })

    return items


async def create_staff(db: AsyncSession, data: ReceptionCreate):
    """新增运营人员，并保证这个人有登录账号（账号 = 手机号，初始密码 123456）。

    两种情况：
    - 该手机号下**已经有**一个运营账号（历史上只注册了账号、没建档案的）→
      直接认领：沿用原账号，不改它的密码、也不新建账号，只把档案补上；
    - 没有 → 新开一个账号。

    认领这一步是必须的：如果无脑新建，`open_login_account` 会撞名成
    `手机号_2`，于是同一个人手里两个账号，原来那个还留在列表里删不掉。

    档案与账号同一次 commit：任一步失败整体回滚，
    不会留下「有账号没档案」（登录后处处 404）或「有档案没账号」的半截数据。
    返回 (档案, 登录名, 是否认领了已有账号)。
    """
    occupied = await db.scalar(select(Reception).where(Reception.phone == data.phone))
    if occupied:
        raise HTTPException(
            status_code=400, detail=f"手机号 {data.phone} 已有运营人员档案，请勿重复添加"
        )

    # 同一个手机号理论上可能有多个账号（撞名时 username 会退化成 手机号_2，但 phone 还是同一个），
    # 显式按 id 取最早的那个，别让 MySQL 的返回顺序决定认领到谁
    account = await db.scalar(
        select(User)
        .where(User.role == "reception", User.phone == data.phone)
        .order_by(User.id.asc())
        .limit(1)
    )
    adopted = account is not None
    if account:
        username = account.username
    else:
        account, username = await open_login_account(
            db, name=data.name, phone=data.phone, role="reception"
        )

    staff = Reception(
        user_id=account.id,
        name=data.name,
        phone=data.phone,
        salary=data.salary,
        hire_date=data.hire_date,
        status=data.status or "在职",
        remark=data.remark,
    )
    db.add(staff)
    await db.commit()
    await db.refresh(staff)
    return staff, username, adopted


async def delete_staff(db: AsyncSession, staff_id: int):
    """删除运营人员，并连带删除其登录账号。

    返回被删者的姓名；找不到时返回 None（接口层回 404）。
    与「删除教练」一致：reception.user_id 的外键是 SET NULL，
    不主动删账号的话，sys_user 里会剩下一个登进去什么都看不到的孤儿账号。
    """
    staff = await db.scalar(select(Reception).where(Reception.id == staff_id))
    if not staff:
        return None
    name = staff.name
    if staff.user_id:
        account = await db.get(User, staff.user_id)
        if account:
            await db.delete(account)
    await db.delete(staff)
    await db.commit()
    return name


async def delete_staff_account(db: AsyncSession, user_id: int):
    """删除一条「还没建档案」的运营账号，返回账号名。

    只收拾裸账号：账号不存在、或不是运营角色时返回 None（接口层回 404）；
    已经挂了档案的会抛 400，那种要按档案删（走 delete_staff），
    否则会留下一行没有账号、谁也登不进去的孤儿档案。
    """
    account = await db.scalar(
        select(User).where(User.id == user_id, User.role == "reception")
    )
    if not account:
        return None
    has_profile = await db.scalar(
        select(func.count(Reception.id)).where(Reception.user_id == user_id)
    )
    if has_profile:
        raise HTTPException(
            status_code=400,
            detail=f"账号「{account.username}」已建立人员档案，请在列表里删除该运营人员",
        )
    username = account.username
    await db.delete(account)
    await db.commit()
    return username


