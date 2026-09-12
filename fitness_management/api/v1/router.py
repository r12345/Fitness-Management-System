"""API 路由统一注册入口。"""
import re

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

# 教练工作台：接口只在 coach_panel 模块里声明一次，这里把同一个 router 挂到两个前缀下。
# 中划线 /coach-panel 是接口文档的写法，下划线 /coach_panel 是前端在用的历史写法，
# 两个前缀都保留，前端无需改动即可切换。
from fitness_management.api.v1.coach_panel import router as coach_panel_routes


def _operation_id_prefix(prefix: str):
    """生成 ``{prefix}_{视图函数名}`` 形式的 operationId。

    FastAPI 默认用「视图函数名 + 未加前缀的路径」生成 operationId，
    同一个 router 挂两次会撞名，因此两个前缀各用一个前缀词区分。
    """

    def generate(route) -> str:
        return re.sub(r"\W", "_", f"{prefix}_{route.name}")

    return generate


coach_panel_router = APIRouter(prefix='/api/v1/coach-panel', tags=['教练工作台'])
coach_panel_router.include_router(
    coach_panel_routes,
    generate_unique_id_function=_operation_id_prefix("panel"),
)

coach_panel_legacy_router = APIRouter(prefix='/api/v1/coach_panel', tags=['教练工作台'])
coach_panel_legacy_router.include_router(
    coach_panel_routes,
    generate_unique_id_function=_operation_id_prefix("panel_legacy"),
)

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

schedule_router = APIRouter(prefix='/api/v1/schedule', tags=['排班管理'])
from fitness_management.api.v1 import schedule

system_router = APIRouter(prefix='/api/v1/system', tags=['系统配置、日志与字典'])
from fitness_management.api.v1 import system

dashboard_router = APIRouter(prefix='/api/v1/dashboard', tags=['管理员数据大盘'])
from fitness_management.api.v1 import dashboard

reception_router = APIRouter(prefix='/api/v1/reception', tags=['前台管理'])
from fitness_management.api.v1 import reception