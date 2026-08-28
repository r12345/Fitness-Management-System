"""API 路由统一注册入口。"""
# 创建路由
from fastapi import APIRouter
user_router = APIRouter(prefix='/api/v1/auth', tags=['登录'])
from fitness_management.api.v1 import auth
