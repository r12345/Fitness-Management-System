"""FastAPI 主入口。"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import fitness_management.models  # noqa: F401  导入models模块，确保模型类被注册到Base的metadata中
from fitness_management.api.v1.router import (
    appointments_router,
    coach_panel_legacy_router,
    coach_panel_router,
    coaches_router,
    consumptions_router,
    courses_router,
    equipment_router,
    member_center_router,
    members_router,
    schedule_router,
    statistics_router,
    system_router,
    training_router,
    user_router, dashboard_router, reception_router,
)
from fitness_management.utils.res import BizError, biz_error_handler

app = FastAPI(title="健身管理系统")

app.include_router(user_router)
app.include_router(members_router)
app.include_router(member_center_router)
app.include_router(courses_router)
app.include_router(coaches_router)
app.include_router(coach_panel_router)
app.include_router(coach_panel_legacy_router)
app.include_router(appointments_router)
app.include_router(training_router)
app.include_router(equipment_router)
app.include_router(statistics_router)
app.include_router(consumptions_router)
app.include_router(schedule_router)
app.include_router(system_router)
app.include_router(dashboard_router)
app.include_router(reception_router)

# 业务异常统一转换为 {"code", "msg", "data"} 响应
app.add_exception_handler(BizError, biz_error_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发环境允许全部来源，生产不要*
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 在应用启动时创建所有定义的表
# async def create_tables():
#     async with async_engine.begin() as conn:
#         await conn.run_sync(models.Base.metadata.create_all)
#
# @app.on_event("startup")
# async def startup_event():
#     await create_tables()

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001)
