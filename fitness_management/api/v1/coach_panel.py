"""教练工作台接口。"""
from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .router import coach_panel_router
from ...core.database import get_db
from ...core.security import get_current_user
from ...crud.coach_panel import get_my_schedule, create_schedule
from ...crud.training import list_my_plans, create_plan, update_plan
from ...models import Coach, User
from ...schemas.coach_panel import ScheduleCreate
from ...schemas.training import PlanCreate, PlanUpdate, PlanItem, PlanItemSelf
from ...utils.res import success_response


async def _get_current_coach(db: AsyncSession, user: User) -> Coach:
    """根据登录用户查找对应的教练档案。"""
    coach = await db.scalar(select(Coach).where(Coach.user_id == user.id))
    if not coach:
        raise HTTPException(status_code=404, detail="未找到教练档案")
    return coach


@coach_panel_router.get('/schedules')
async def get_coach_schedules(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """获取当前教练的排课列表。"""
    coach = await _get_current_coach(db, user)
    data = await get_my_schedule(db, coach.id)
    return success_response(data=data)


@coach_panel_router.post('/schedules')
async def post_coach_schedules(
    schedule: ScheduleCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """当前教练新增排课。"""
    coach = await _get_current_coach(db, user)
    created = await create_schedule(db, coach.id, schedule)
    if created is None:
        raise HTTPException(status_code=400, detail="课程不存在")
    await db.commit()
    return success_response(msg="排课成功", data={
        "id": created.id,
        "coach_id": created.coach_id,
        "course_id": created.course_id,
        "schedule_date": created.schedule_date,
        "start_time": created.start_time,
        "end_time": created.end_time,
        "location": created.location,
        "booked_count": created.booked_count,
        "status": created.status,
    })


# ===== 14. 训练计划 =====
@coach_panel_router.get('/plans')
async def list_coach_plans(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """14.1 训练计划列表（当前教练创建的）。"""
    coach = await _get_current_coach(db, user)
    plans = await list_my_plans(db, coach.id)
    return success_response(data=[PlanItemSelf.model_validate(p).model_dump(mode="json") for p in plans])


@coach_panel_router.post('/plans')
async def create_coach_plan(
    plan: PlanCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """14.2 制定训练计划。"""
    coach = await _get_current_coach(db, user)
    created = await create_plan(db, coach.id, plan)
    await db.commit()
    return success_response(msg="制定成功", data=PlanItem.model_validate(created).model_dump(mode="json"))


@coach_panel_router.put('/plans/{plan_id}')
async def update_coach_plan(
    plan_id: int,
    plan: PlanUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """14.3 编辑训练计划。"""
    coach = await _get_current_coach(db, user)
    updated = await update_plan(db, plan_id, coach.id, plan)
    if not updated:
        raise HTTPException(status_code=404, detail="计划不存在")
    await db.commit()
    return success_response(msg="编辑成功", data=PlanItem.model_validate(updated).model_dump(mode="json"))
