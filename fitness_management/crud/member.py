"""会员相关数据库操作。"""
import datetime
from datetime import timedelta
from typing import Optional

from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import HTTPException

from fitness_management.models import Member, ConsumeRecord, Appointment, CheckinRecord, User
from fitness_management.schemas.member import MemberRequest, RenewMember
from fitness_management.crud.user import open_login_account


# 会员卡状态的唯一权威是 card_expire（到期时间），status 只是它的派生值：
#     card_expire 未到 → 正常；已过 → 过期
# 唯一例外是「暂停」：那是人工意图（例如会员请假停卡），自动同步不能覆盖它。
CARD_ACTIVE = "正常"
CARD_EXPIRED = "过期"
CARD_SUSPENDED = "暂停"
# 人工维护的状态集合，自动同步时要跳过
MANUAL_CARD_STATUSES = frozenset({CARD_SUSPENDED})


def calc_card_status(card_expire, current: Optional[str] = None) -> str:
    """按到期时间推导卡状态。

    current 传「暂停」时原样返回——人工状态优先于自动判定。
    card_expire 允许传 date 或 datetime（请求体与 ORM 的类型不完全一致）。
    """
    if current in MANUAL_CARD_STATUSES:
        return current
    if card_expire is None:
        return CARD_ACTIVE
    expire = card_expire.date() if isinstance(card_expire, datetime.datetime) else card_expire
    return CARD_EXPIRED if expire < datetime.date.today() else CARD_ACTIVE


async def sync_card_statuses(db: AsyncSession, member_id: Optional[int] = None) -> int:
    """把 status 与 card_expire 不一致的会员卡归正，返回修正条数。

    读列表/详情前惰性调用一次即可：没人会记得去点「同步」按钮，
    放在查询前自动执行，状态才会永远跟到期时间一致。
    """
    stmt = select(Member).where(Member.status.notin_(list(MANUAL_CARD_STATUSES)))
    if member_id is not None:
        stmt = stmt.where(Member.id == member_id)
    result = await db.execute(stmt)
    fixed = 0
    for member in result.scalars().all():
        want = calc_card_status(member.card_expire, member.status)
        if member.status != want:
            member.status = want
            fixed += 1
    if fixed:
        await db.commit()
    return fixed


async def show_all_members(page, page_size, keyword, status, card_type, db: AsyncSession):
    # 先按到期时间归正状态，再按状态过滤：否则「已过期但标着正常」的会员
    # 既不会出现在「过期」筛选里，又会混进「正常」列表。
    await sync_card_statuses(db)

    limit = page_size
    offset = (page - 1) * page_size
    # 基础查询语句
    stmt = select(Member)

    # 🔹关键词：姓名模糊 OR 手机号模糊，有值才追加条件
    if keyword:
        stmt = stmt.where(
            or_(
                Member.name.like("%" + keyword + "%"),
                Member.phone.like("%" + keyword + "%")
            )
        )
    # 🔹卡状态过滤，有值才追加
    if status:
        stmt = stmt.where(Member.status == status)
    # 🔹办卡类型过滤，有值才追加
    if card_type:
        stmt = stmt.where(Member.card_type == card_type)
    # 🔹统计总条数
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = await db.scalar(count_stmt)
    # 分页
    stmt = stmt.limit(limit).offset(offset)
    result = await db.execute(stmt)
    members = result.scalars().all()

    return members,total


async def get_total(db:AsyncSession):
    query = select(func.count(Member.id))
    result = await db.execute(query)
    total = result.scalar()
    return total


# 创建用户
async def add_member(member: MemberRequest, db: AsyncSession):
    """前台/管理员新增会员（开卡）。

    以前只插 member 表一条档案，会员拿手机号登录不了，进不去会员中心 ——
    会员自己看打卡、预约、训练计划的那些功能全用不上。
    现在顺带开一个登录账号（账号=手机号，初始密码见 DEFAULT_PASSWORD），
    账号与档案同一次 commit，失败整体回滚。
    """
    account, username = await open_login_account(
        db, name=member.name, phone=member.phone, role="member"
    )
    member_row = Member(
        user_id=account.id,
        name=member.name,
        phone=member.phone,
        gender=member.gender,
        age=member.age,
        card_type=member.card_type,
        card_start=member.card_start,
        card_expire=member.card_expire,
        balance=member.balance,
        # 状态跟着到期时间走，不再信表单里填的值（「暂停」除外）
        status=calc_card_status(member.card_expire, member.status),
        remark=member.remark,
        # 归属教练：前台办卡时可指定，不指定就是无人带
        coach_id=member.coach_id,
        )
    db.add(member_row)
    await db.commit()
    await db.refresh(member_row)
    return member_row, username


async def assign_student(coach_id: int, member_id: int, db: AsyncSession):
    """教练把一名**已有会员**挂到自己名下，成为自己的学员。

    教练不再自己造会员档案：会员要么是前台开卡时建的、要么本人注册的，
    两者都已经带登录账号。教练这边只负责「认领」，也就不会出现
    「教练新建的学员没有账号、登不进会员中心」这种半截数据。

    返回 ``None`` 表示会员不存在（接口层回 404）；
    会员已归属其他教练时抛 400 —— 改派是前台/管理员的活（会员管理的「编辑」里有归属教练）。
    """
    member = await db.scalar(select(Member).where(Member.id == member_id))
    if not member:
        return None
    if member.coach_id is not None and member.coach_id != coach_id:
        raise HTTPException(status_code=400, detail="该会员已归属其他教练，请先在前台改派")
    member.coach_id = coach_id
    await db.commit()
    await db.refresh(member)
    return member


async def delete_member(member_id: int, db: AsyncSession):
    query = select(Member).where(Member.id == member_id)
    result = await db.execute(query)
    member = result.scalar()
    if not member:
        return False
    # 联动删除关联的登录账号：member.user_id 的外键是 ON DELETE SET NULL，
    # 不主动删的话 sys_user 里会剩下一个能登录、但每个会员接口都 404
    # 「未找到会员档案」的孤儿账号。与「删除教练」的处理保持一致。
    user_id = member.user_id
    if user_id:
        account = await db.get(User, user_id)
        if account:
            await db.delete(account)
    await db.delete(member)
    await db.commit()
    return True


async def renew_card(member_id: int,renew_info:RenewMember,db: AsyncSession,user:User):
    query = select(Member).where(Member.id == member_id)
    result = await db.execute(query)
    member = result.scalar_one_or_none()
    if not member:
        return None
    # 原来先累加余额再判断 `member.balance >= 0`：既拦不住负数金额（余额够就能过），
    # 又会把金额提前写进 ORM 对象。接口层的错误文案本来就写的是「金额小于0」，按它来。
    if renew_info.amount < 0:
        return None

    member.balance += renew_info.amount
    today = datetime.date.today()
    if member.card_expire < today:
        # 已过期：从今天重新起算，而不是在旧的过期日上叠加
        member.card_expire = today + timedelta(days=30 * renew_info.months)
    else:
        member.card_expire += timedelta(days=30 * renew_info.months)
    member.card_type = renew_info.card_type
    # 续卡后到期日必然在未来，状态跟着回到「正常」（人工「暂停」保留）
    member.status = calc_card_status(member.card_expire, member.status)
    await db.commit()

    operator = renew_info.operator
    if operator == '':
        operator = user.name
    consume_record = ConsumeRecord(
        member_id=member.id,
        item=renew_info.remark,
        amount=renew_info.amount,
        pay_method=renew_info.pay_method,
        operator=operator,
        created_at=datetime.datetime.now(),
        member=member
    )
    db.add(consume_record)
    await db.commit()
    await db.refresh(consume_record)
    return [member, consume_record]


async def get_member_by_user(db: AsyncSession, user: User) -> Member:
    """取当前登录用户对应的会员档案（会员角色专用）。

    查不到就抛 404 —— 「登录账号没有会员档案」这个错误在每个会员接口里
    都得拦一次，放在这里统一收口，接口层不必各写一份 try/if。

    原先是两处私有函数：api/v1/appointments.py 的 ``_get_current_member_id``
    和 api/v1/training.py 的 ``_get_current_member``，查的是同一张表、同一条件、
    同一个错误文案；前者只是多取了一步 ``.id``。
    """
    member = await db.scalar(select(Member).where(Member.user_id == user.id))
    if not member:
        raise HTTPException(status_code=404, detail="未找到会员档案")
    return member


async def getOneMember(member_id: int, db: AsyncSession):
    query = select(Member).where(Member.id == member_id)
    result = await db.execute(query)
    member = result.scalar_one_or_none()
    if member:
        # 详情页也要看到与到期时间一致的状态
        await sync_card_statuses(db, member_id=member_id)
        await db.refresh(member)
    return member


async def getDetailMember(member_id: int, db: AsyncSession):
        query = select(ConsumeRecord).where(ConsumeRecord.member_id == member_id)
        result = await db.execute(query)
        records = result.scalars().all()
        query2 = select(Appointment).where(Appointment.member_id == member_id)
        result2 = await db.execute(query2)
        appointments = result2.scalars().all()
        query3 = select(CheckinRecord).where(CheckinRecord.member_id == member_id)
        result3 = await db.execute(query3)
        checkins = result3.scalars().all()
        return records,appointments,checkins


# 修改用户
async def updateMember(member_id: int, member: MemberRequest, db: AsyncSession):
    query = select(Member).where(Member.id == member_id)
    result = await db.execute(query)
    member_db = result.scalar_one_or_none()
    if member_db:
        member_db.name = member.name
        member_db.phone = member.phone
        member_db.gender = member.gender
        member_db.age = member.age
        member_db.card_type = member.card_type
        member_db.card_start = member.card_start
        member_db.card_expire = member.card_expire
        member_db.balance = member.balance
        # 改了到期时间，状态要跟着重算，否则会出现「延期到明年、状态还是过期」
        member_db.status = calc_card_status(member.card_expire, member.status)
        member_db.remark = member.remark
        # 归属教练：前台/管理员可以改派（教练自己拉来的学员也允许被改派）。
        # 只有请求体里**显式带了** coach_id 才覆盖 —— 否则「编辑一下手机号」
        # 会把这位会员的归属教练悄悄清空，他的教练在工作台上就找不到这个学员了。
        if "coach_id" in member.model_fields_set:
            member_db.coach_id = member.coach_id
        await db.commit()
        return True
    return False


async def updateMemberStatus(id, status, db: AsyncSession):
    """人工改卡状态。返回实际生效的状态字符串；会员不存在时返回 None。

    只有「暂停」是人工语义；想设成「正常/过期」时一律按到期时间归正，
    避免手填出「卡已过一年却标着正常」这种自相矛盾的数据。
    """
    query = select(Member).where(Member.id == id)
    result = await db.execute(query)
    member = result.scalar_one_or_none()
    if not member:
        return None
    member.status = calc_card_status(member.card_expire, status.status)
    await db.commit()
    return member.status
