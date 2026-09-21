import datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fitness_management.core.security import get_password_hash,verify_password
from fitness_management.models import User, Member, Coach, Reception
from fitness_management.schemas.auth import AuthRequest, UserInfoRequest


# 管理员/前台在后台「新增教练」「新增会员」时，系统会顺手开一个能登录的账号。
# 这类账号的初始密码统一用这个值：办卡、入职大多是线下当面办理，
# 让被添加的人自己先注册一遍不现实，先给个默认密码，登录后自行修改。
DEFAULT_PASSWORD = "123456"


#检查用户名存在
async def check_user_exists(username,db:AsyncSession):
    # 检查数据库中是否存在该用户名
    query = select(User).where(User.username == username)
    # 如果存在，返回True
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    if user:
        return True
    return False


async def build_unique_username(db: AsyncSession, phone: str, name: str = "") -> str:
    """按手机号生成一个未被占用的登录账号。

    用手机号而不是姓名：姓名会重复（同名会员很常见），手机号才是现实里
    能唯一对应到人的东西，用户也记得住 —— 「手机号 + 123456」就是默认凭据。
    万一手机号已被注册（例如本人先自助注册过），就退化成 手机号_2、手机号_3。
    """
    base = (phone or "").strip() or (name or "").strip() or "user"
    candidate = base
    index = 1
    while await check_user_exists(candidate, db):
        index += 1
        candidate = f"{base}_{index}"
    return candidate


async def open_login_account(
    db: AsyncSession, name: str, phone: str, role: str
) -> tuple[User, str]:
    """为「后台新增的人」开一个登录账号，返回 (账号对象, 登录名)。

    只 add + flush，不 commit —— 调用方要把「账号 + 档案（教练/会员）」
    放在同一个事务里提交，避免出现「有账号没档案」（登录后处处 404）或
    「有档案没账号」（老问题：新增的人根本没法登录）的半截数据。
    提交时机与 register_user 的做法保持一致。
    """
    username = await build_unique_username(db, phone, name)
    account = User(
        username=username,
        password_hash=get_password_hash(DEFAULT_PASSWORD),
        role=role,
        name=name,
        phone=phone,
        status="启用",
        created_at=datetime.datetime.now(),
    )
    db.add(account)
    await db.flush()
    return account, username


# 注册用户

async def register_user(user_info:UserInfoRequest,db:AsyncSession):
        # 创建新用户
        # hash密码
        password_hash=get_password_hash(user_info.password)
        user = User(username=user_info.username,
                    password_hash=password_hash,
                    role=user_info.role,
                    name=user_info.name,
                    phone=user_info.phone,
                    status=user_info.status,
                    created_at=datetime.datetime.now()
                   )
        # 将用户添加到数据库
        db.add(user)
        # 先 flush 拿到 user.id，再建档案，最后统一 commit。
        # 原先是先 commit 用户、再 add 档案，靠 get_db 结尾的隐式 commit 兜底：
        # 一旦档案写入失败就会留下「有登录账号、没有档案」的用户，
        # 会员中心 / 教练工作台随后全部 404。另外 reception 分支当时漏了 db.add，
        # 前台注册后永远没有档案，登录返回的 role_id 也是 null。
        await db.flush()

        today = datetime.date.today()
        if user_info.role == 'member':
            # 注册即开一张 30 天有效的体验卡。
            # 原来写的是 status='过期' + card_expire=now，注册完连一节课都约不了。
            member = Member(user_id=user.id, name=user.name, phone=user.phone,
                            card_type='次卡', card_start=today,
                            card_expire=today + datetime.timedelta(days=30),
                            balance=0, status='正常')
            db.add(member)
        elif user_info.role == 'coach':
            coach = Coach(user_id=user.id,name=user.name,phone=user.phone,status='在职',specialties='无',hire_date=today)
            db.add(coach)
        elif user_info.role == 'reception':
            reception = Reception(user_id=user.id,name=user.name,phone=user.phone,status='在职',hire_date=today)
            db.add(reception)

        await db.commit()
        return user
    # 如果存在，返回错误信息
    # 如果不存在，创建新用户并返回成功信息


async def change_password(db: AsyncSession, user: User, old_password: str, new_password: str) -> User:
    """本人修改自己的登录密码。

    必须先验当前密码：只知道 token 的人（比如借用了未退出的电脑）不该能直接
    把密码改掉、把真正的机主关在门外。
    改的是哈希列，明文在任何地方都不落库。
    """
    if not verify_password(old_password, user.password_hash):
        raise HTTPException(status_code=400, detail="当前密码不正确")
    user.password_hash = get_password_hash(new_password)
    await db.commit()
    await db.refresh(user)
    return user


# 登录
async def login_user(user_info:AuthRequest,db:AsyncSession):
    # 检查数据库中是否存在该用户名
    query = select(User).where(User.username == user_info.username)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    # 如果存在，检查密码是否正确
    if user and verify_password(user_info.password, user.password_hash) and user.role == user_info.role:
        # 如果密码正确，返回用户信息
        return user
    # 如果用户不存在或密码不正确，返回错误信息
    return None


async def get_role_id(user,db:AsyncSession):
    if user.role == 'member':
        query = select(Member).where(Member.user_id == user.id)
        result = await db.execute(query)
        member = result.scalar_one_or_none()
        if member is None:
            return None
        return member.id
    elif user.role == 'coach':
        query = select(Coach).where(Coach.user_id == user.id)
        result = await db.execute(query)
        coach = result.scalar_one_or_none()
        if coach is None:
            return None
        return coach.id
    elif user.role == 'reception':
        query = select(Reception).where(Reception.user_id == user.id)
        result = await db.execute(query)
        reception = result.scalar_one_or_none()
        if reception is None:
            return None
        return reception.id
    else:
        return None


