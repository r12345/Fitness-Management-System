"""密码加密、JWT Token 生成与校验。"""
from datetime import datetime, timedelta, timezone

from fastapi import Header, Depends, HTTPException
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fitness_management.core.config import settings
from fitness_management.core.database import get_db
from fitness_management.models import Coach, User

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def _now() -> datetime:
    """带时区的当前时间。

    原来用的是 ``datetime.utcnow()``：Python 3.12 起已被弃用（会有 DeprecationWarning），
    而且返回的是 naive 时间，写进 JWT 的 ``exp`` 时说不清是哪个时区。
    """
    return datetime.now(timezone.utc)


def create_access_token(subject: str):
    expire = _now() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(
        {"sub": subject, "exp": expire, "type": "access"},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

def create_refresh_token(subject: str):
    # 原来两种 Token 的载荷完全一样（只差 exp），refresh token 可以直接当 access token 用。
    # 加 type 区分后，刷新端点做出来才能真正生效。
    expire = _now() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return jwt.encode(
        {"sub": subject, "exp": expire, "type": "refresh"},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


async def get_current_user(authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    """从 Authorization 请求头解析 JWT，返回当前登录用户。

    缺少请求头、格式错误、签名/有效期校验失败统一返回 401。
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="用户未登录或Token已过期")
    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        # 老 Token 没有 type 字段，按 access 放行（避免改动后把已登录的会话全部打掉）；
        # 但 refresh token 绝不允许当 access token 用。
        if payload.get("type", "access") != "access":
            raise HTTPException(status_code=401, detail="Token 类型错误，请重新登录")
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
        raise HTTPException(status_code=403, detail="仅教练可访问该接口")
    coach = await db.scalar(select(Coach).where(Coach.user_id == user.id))
    if not coach:
        raise HTTPException(status_code=404, detail="未找到教练档案")
    return coach


def require_roles(*roles: str):
    """角色白名单依赖。

    用法：``user: User = Depends(require_roles("admin", "reception"))``。

    此前绝大多数接口只挂了 ``get_current_user``，也就是说**任何登录用户都能调**：
    会员拿自己的 Token 就能删教练、改系统配置、看管理员大盘。前端路由守卫挡得住点击，
    挡不住直接 curl。这里补上服务端校验。
    """
    async def _checker(user: User = Depends(get_current_user)) -> User:
        if roles and user.role not in roles:
            raise HTTPException(status_code=403, detail="当前角色无权访问该接口")
        return user

    return _checker
