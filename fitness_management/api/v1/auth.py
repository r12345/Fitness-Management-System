"""登录、退出、密码重置与个人信息接口。"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from fitness_management.crud.user import check_user_exists, register_user, login_user
from fitness_management.schemas.auth import AuthRequest

from .router import user_router
from ...core.database import get_db


@user_router.post('/login')
async def login(user_info:AuthRequest,db=Depends(get_db)):
    # 检查用户是否存在
    flag1 = await check_user_exists(user_info.username, db)
    if flag1 is False:
        return {"message": "用户不存在"}
    # 登录用户
    user = await login_user(user_info, db)
    if user is None:
        return {"message": "用户名或密码错误"}
    return {"message": "登录成功"}


@user_router.post('/register')
async def register(user_info: AuthRequest,db=Depends(get_db)):
    #  检查用户是否存在
    flag1=await check_user_exists(user_info.username, db)
    if flag1 is True:
        return {"message": "用户已存在"}
    # 注册用户
    user = await register_user(user_info, db)
    if user:
        return {"message": "注册成功"}
    return {"message": "注册失败"}
