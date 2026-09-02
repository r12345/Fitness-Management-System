"""API 路由统一注册入口。"""
# 创建路由
from fastapi import APIRouter
user_router = APIRouter(prefix='/api/v1/auth', tags=['登录'])
from fitness_management.api.v1 import auth

members_router = APIRouter(prefix='/api/v1/members', tags=['会员管理'])
from fitness_management.api.v1 import members

member_center_router = APIRouter(prefix='/api/v1/member_center', tags=['会员中心'])
from fitness_management.api.v1 import member_center

courses_router = APIRouter(prefix='/api/v1/courses', tags=['课程管理'])
from fitness_management.api.v1 import courses