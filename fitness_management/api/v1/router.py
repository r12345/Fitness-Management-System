"""API 路由统一注册入口。"""
# 创建路由
from fastapi import APIRouter
user_router = APIRouter(prefix='/api/v1/auth', tags=['登录'])
from fitness_management.api.v1 import auth

members_router = APIRouter(prefix='/api/v1/members', tags=['会员管理'])
from fitness_management.api.v1 import members

member_center_router = APIRouter(prefix='/api/v1/member_center', tags=['会员中心'])
from fitness_management.api.v1 import member_center

coaches_router = APIRouter(prefix='/api/v1/coaches', tags=['教练管理接口'])
from fitness_management.api.v1 import coaches


courses_router = APIRouter(prefix='/api/v1/courses', tags=['课程管理'])
from fitness_management.api.v1 import courses

coach_panel_router = APIRouter(prefix='/api/v1/coach_panel', tags=['教练工作台'])
from fitness_management.api.v1 import coach_panel


consumptions_router = APIRouter(prefix='/api/v1/consumptions', tags=['消费管理'])
from fitness_management.api.v1 import consumption

equipment_router = APIRouter(prefix='/api/v1/equipment', tags=['器材管理'])
from fitness_management.api.v1 import equipment

statistics_router = APIRouter(prefix='/api/v1/statistics', tags=['运营数据'])
from fitness_management.api.v1 import statistics

training_router = APIRouter(prefix='/api/v1/training', tags=['训练打卡与运动记录'])
from fitness_management.api.v1 import training


