"""FastAPI 主入口：只做装配，不写业务逻辑。

这里只保留四件事：
    1. 建 ``app``
    2. 挂启动钩子（实现见 core/lifespan.py）
    3. 注册各业务模块路由（分组与前缀见 api/v1/router.py）
    4. 注册异常处理器（见 utils/exception_handlers.py、utils/res.py）与 CORS

具体实现都在各自目录里，main.py 里不定义函数、也不写路由。
"""
import uvicorn
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

import fitness_management.models  # noqa: F401  导入models模块，确保模型类被注册到Base的metadata中
from fitness_management.api.v1.router import (
    agent_router,
    appointments_router,
    coach_panel_router,
    coaches_router,
    consumptions_router,
    courses_router,
    dashboard_router,
    equipment_router,
    member_center_router,
    members_router,
    reception_router,
    statistics_router,
    system_router,
    training_router,
    user_router,
)
from fitness_management.core.lifespan import lifespan
from fitness_management.core.operation_log import OperationLogMiddleware
from fitness_management.utils.exception_handlers import (
    unhandled_error_handler,
    validation_error_handler,
)
from fitness_management.utils.res import BizError, biz_error_handler

app = FastAPI(title="健身管理系统", lifespan=lifespan)

# 各业务模块路由，前缀与分组标签在 api/v1/router.py 中声明
app.include_router(user_router)              # /api/v1/auth             登录           x
app.include_router(members_router)           # /api/v1/members          会员管理        x
app.include_router(member_center_router)     # /api/v1/member_center    会员中心        x
app.include_router(courses_router)           # /api/v1/courses          课程管理        y
app.include_router(coaches_router)           # /api/v1/coaches          教练管理         r
app.include_router(coach_panel_router)       # /api/v1/coach-panel      教练工作台       r
app.include_router(appointments_router)      # /api/v1/appointments     预约管理         r
app.include_router(training_router)          # /api/v1/training         训练打卡与运动记录 y
app.include_router(equipment_router)         # /api/v1/equipment        器材管理        x
app.include_router(statistics_router)        # /api/v1/statistics       运营数据        y
app.include_router(consumptions_router)      # /api/v1/consumption      消费记录        x
app.include_router(system_router)            # /api/v1/system           系统配置、日志与字典r
app.include_router(dashboard_router)         # /api/v1/dashboard        管理员数据大盘     y
app.include_router(reception_router)         # /api/v1/reception        前台管理        x
app.include_router(agent_router)             # /api/v1/agent            AI 助手（扣子令牌） r

# 异常统一转换：业务异常走 {"code", "msg", "data"}，参数校验与兜底 500 走 {"detail"}
app.add_exception_handler(BizError, biz_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(Exception, unhandled_error_handler)

# 操作日志中间件：把超级管理员 / 前台运营 / 健身教练 / 普通会员的写操作记进 sys_log。
# 必须注册在 CORS **之前** —— add_middleware 是「后注册的更靠外」，
# 这样 CORS 仍是最外层，日志中间件万一出问题也不会让响应丢掉跨域头。
app.add_middleware(OperationLogMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发环境允许全部来源，生产不要*
    # 通配符来源 + allow_credentials=True 是规范上不允许的组合（浏览器会直接拒绝携带凭据的跨域请求）。
    # 本项目鉴权走 Authorization 请求头，不依赖 Cookie，所以关掉凭据即可。
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001)
