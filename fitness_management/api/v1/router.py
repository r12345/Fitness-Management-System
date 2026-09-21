"""API 路由统一注册入口。

每个模块在这里声明一个 ``APIRouter``（前缀 + 分组标签），
模块内部用 ``@xxx_router.get(...)`` 注册具体接口，
最后在 ``main.py`` 里统一 ``app.include_router(...)`` 挂载。
"""
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

coach_panel_router = APIRouter(prefix='/api/v1/coach-panel', tags=['教练工作台'])
from fitness_management.api.v1 import coach_panel

appointments_router = APIRouter(prefix='/api/v1/appointments', tags=['预约管理'])
from fitness_management.api.v1 import appointments

training_router = APIRouter(prefix='/api/v1/training', tags=['训练打卡与运动记录'])
from fitness_management.api.v1 import training

equipment_router = APIRouter(prefix='/api/v1/equipment', tags=['器材管理'])
from fitness_management.api.v1 import equipment

consumptions_router = APIRouter(prefix='/api/v1/consumption', tags=['消费记录'])
from fitness_management.api.v1 import consumption

statistics_router = APIRouter(prefix='/api/v1/statistics', tags=['运营数据'])
from fitness_management.api.v1 import statistics

system_router = APIRouter(prefix='/api/v1/system', tags=['系统配置、日志与字典'])
from fitness_management.api.v1 import system

dashboard_router = APIRouter(prefix='/api/v1/dashboard', tags=['管理员数据大盘'])
from fitness_management.api.v1 import dashboard

reception_router = APIRouter(prefix='/api/v1/reception', tags=['前台管理'])
from fitness_management.api.v1 import reception

agent_router = APIRouter(prefix='/api/v1/agent', tags=['AI 助手'])
from fitness_management.api.v1 import agent
