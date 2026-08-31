"""FastAPI 主入口。"""
import uvicorn
from fastapi import FastAPI
from core.database import async_engine
import models  # 导入您的models模块，确保模型类被注册到Base的metadata中
from fitness_management.api.v1.router import user_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.include_router(user_router)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  #开发环境允许全部来源，生产不要*
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
    uvicorn.run(app, host="127.0.0.1", port=8000)
