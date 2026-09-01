import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fitness_management.core.security import get_password_hash,verify_password
from fitness_management.models import User, Member, Coach, Reception
from fitness_management.schemas.auth import AuthRequest, UserInfoRequest


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
        await db.commit()
        if user:
            if user_info.role == 'member':
                # 如果是会员，添加会员表记录
                member = Member(user_id=user.id,name=user.name,phone=user.phone,card_type='次卡',card_expire=datetime.datetime.now(),status='过期')
                db.add(member)
            elif user_info.role == 'coach':
                coach = Coach(user_id=user.id,name=user.name,phone=user.phone,status='空闲',specialties='无',hire_date=datetime.datetime.now())
                db.add(coach)
            elif user_info.role == 'reception':
                reception = Reception(user_id=user.id,name=user.name,phone=user.phone,status='空闲',hire_date=datetime.datetime.now())
        return user
    # 如果存在，返回错误信息
    # 如果不存在，创建新用户并返回成功信息


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