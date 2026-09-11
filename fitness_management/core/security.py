"""密码加密、JWT Token 生成与校验。"""
from datetime import datetime, timedelta

from fastapi import Header, Depends, HTTPException
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fitness_management.core.config import settings
from fitness_management.core.database import get_db
from fitness_management.models import Coach, User
from fitness_management.utils.codes import COACH_NOT_FOUND, PERMISSION_DENIED
from fitness_management.utils.res import BizError

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: str):
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub": subject, "exp": expire}, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def create_refresh_token(subject: str):
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return jwt.encode({"sub": subject, "exp": expire}, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


async def get_current_user(authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    """从 Authorization 请求头解析 JWT，返回当前登录用户。

    缺少请求头、格式错误、签名/有效期校验失败统一返回 401。
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="用户未登录或Token已过期")
    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = int(payload["sub"])
    except (JWTError, KeyError, TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Token 无效或已过期")

    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在或注销")
    return user


async def get_current_coach(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Coach:
    """在当前登录用户基础上解析出教练档案。

    教练工作台与排班管理都需要「当前登录教练」，这里集中一处，
    避免各模块各写一份；非 ``role=coach`` 返回 403，
    角色正确但没有教练档案返回 404。
    """
    if user.role != "coach":
        raise BizError("仅教练可访问该接口", code=PERMISSION_DENIED, status_code=403)
    coach = await db.scalar(select(Coach).where(Coach.user_id == user.id))
    if not coach:
        raise BizError("未找到教练档案", code=COACH_NOT_FOUND, status_code=404)
    return coach




