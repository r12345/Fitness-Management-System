"""应用启动 / 关闭钩子。

放在 core 下、与 database.py 同级：这里的逻辑只有一件事 ——
进程启动时建数据库会话，把「随时间变化」的派生状态全量归正一次。
main.py 只负责把它挂到 FastAPI 上，不再承担具体逻辑。
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from fitness_management.core.database import AsyncSessionLocal
from fitness_management.crud.coach_panel import sync_course_schedules, sync_schedule_statuses
from fitness_management.crud.member import sync_card_statuses

# 用 uvicorn 的 logger：默认的 logging 只在 WARNING 以上才输出，
# 这几条启动同步的信息会被咽掉，出了事也看不见。
logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动时把「派生数据」全量归正一次。

    - 课程排课：按课程时间把窗口内（今天前后各 2 周）的排课补齐
    - 会员卡状态：按 card_expire 判定正常/过期
    - 排课状态：按上课时段判定未开始/进行中/已结束

    各读路径还有惰性同步兜底（会员列表/详情、个人中心、预约校验、大盘统计、
    教练工作台排课），但启动这一次能保证库里本身就是干净的——历史上留下的
    「到期日 2099 年却标着过期」「9 月的课状态还写着 normal」这类脏数据，一开机就归位。
    生成要排在状态归正之前：新排好的课还没做过状态判定。
    """
    try:
        async with AsyncSessionLocal() as session:
            created = await sync_course_schedules(session)
            logger.info("课程排课启动同步完成，新生成 %s 条", created)
        async with AsyncSessionLocal() as session:
            fixed_cards = await sync_card_statuses(session)
            logger.info("会员卡状态启动同步完成，修正 %s 条", fixed_cards)
        async with AsyncSessionLocal() as session:
            fixed_schedules = await sync_schedule_statuses(session)
            logger.info("排课状态启动同步完成，修正 %s 条", fixed_schedules)
    except Exception:
        # 同步失败不应该拦住服务启动
        logger.exception("启动同步失败")
    yield
