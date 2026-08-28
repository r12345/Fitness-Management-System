"""登录、退出、密码重置与个人信息接口。"""
from fastapi import APIRouter

router = APIRouter(prefix='/api/v1/auth', tags=['登录'])

@router.post('/login')
async def login():
    