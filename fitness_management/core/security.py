"""密码加密、JWT Token 生成与校验。"""
from datetime import datetime, timedelta

from fastapi import Header, Depends, HTTPException
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fitness_management.core.config import settings
from fitness_management.core.database import get_db
from fitness_management.models import User

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


async def get_current_user(authorization: str = Header(None),db:AsyncSession = Depends(get_db)):
    print('authorization',authorization)
    if not authorization:
        raise HTTPException(status_code=401, detail="用户未登录或Token已过期")
    token = authorization.split(" ")[1]
    token = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])['sub']
    user_id = int(token)
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在或注销")
    return user



