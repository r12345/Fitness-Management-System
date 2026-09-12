"""教练工作台接口（接口文档 §19 教练工作台 / §14 训练计划）。

路径前缀：``/api/v1/coach-panel``

    19.1 GET    /schedules          我的排课
    19.2 POST   /schedules          新增排课
    19.3 GET    /students           我的学员
    19.4 GET    /records            授课记录
    19.5 GET    /plans              训练计划列表
    19.6 POST   /plans              新增训练计划
    14.3 PUT    /plans/{plan_id}    编辑训练计划
"""
from collections.abc import Iterable
from datetime import date as date_type
from typing import Optional

from fastapi import Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .router import coach_panel_router
from ...core.database import get_db
from ...core.security import get_current_coach
from ...crud.coach_panel import (
    create_my_schedule,
    get_my_records,
    get_my_schedules,
    get_my_students,
)
from ...crud.member import getOneMember
from ...crud.training import create_plan, list_my_plans, update_plan
from ...models import Coach, Member, TrainPlan
from ...schemas.coach_panel import (
    MemberBrief,
    MyPlanItem,
    MyRecordItem,
    MyScheduleItem,
    MyStudentItem,
    ScheduleCreate,
)
from ...schemas.training import PlanCreate, PlanUpdate
from ...utils.codes import HTTP_BAD_REQUEST, HTTP_NOT_FOUND, MEMBER_NOT_FOUND
from ...utils.res import BizError, success_response


# ===== 公共工具 =====

def _serialize(model: type[BaseModel], rows: Iterable[dict]) -> list[dict]:
    """按 schema 声明的字段序列化 CRUD 返回的行。

    响应字段因此由 schema 决定，不会随 SQL 查询列的调整而漂移。
    """
    return [model.model_validate(row).model_dump(mode="json") for row in rows]


async def _member_brief(db: AsyncSession, member_id: int) -> Optional[MemberBrief]:
    """按会员编号取简要信息（异步环境下不能用懒加载）。"""
    row = (await db.execute(select(Member.id, Member.name).where(Member.id == member_id))).first()
    return MemberBrief(id=row[0], name=row[1]) if row else None


def _plan_payload(plan: TrainPlan, member: Optional[MemberBrief]) -> dict:
    """训练计划 ORM 对象 → 响应字典。"""
    return MyPlanItem(
        id=plan.id,
        member_id=plan.member_id,
        member_name=member.name if member else None,
        member=member,
        coach_id=plan.coach_id,
        goal=plan.goal,
        body_part=plan.body_part,
        actions=plan.actions,
        sets_reps=plan.sets_reps,
        frequency=plan.frequency,
        start_date=plan.start_date,
        end_date=plan.end_date,
        remark=plan.remark,
    ).model_dump(mode="json")


# ===== 19.1 我的排课 =====

@coach_panel_router.get("/schedules", summary="我的排课")
async def get_coach_schedules(
    status: Optional[str] = Query(None, description="排课状态"),
    schedule_date: Optional[date_type] = Query(None, description="上课日期"),
    coach: Coach = Depends(get_current_coach),
    db: AsyncSession = Depends(get_db),
):
    """获取当前教练的排课列表。"""
    rows = await get_my_schedules(db, coach.id, status=status, schedule_date=schedule_date)
    return success_response(msg="获取成功", data=_serialize(MyScheduleItem, rows))


# ===== 19.2 新增排课 =====

@coach_panel_router.post("/schedules", summary="新增排课")
async def create_coach_schedule(
    schedule: ScheduleCreate,
    coach: Coach = Depends(get_current_coach),
    db: AsyncSession = Depends(get_db),
):
    """当前教练新增排课（只能给自己名下的课程排课，且时段不能重叠）。"""
    created = await create_my_schedule(db, coach.id, schedule)
    await db.commit()
    return success_response(
        msg="排课成功",
        data=MyScheduleItem.model_validate(created).model_dump(mode="json"),
    )


# ===== 19.3 我的学员 =====

@coach_panel_router.get("/students", summary="我的学员")
async def get_coach_students(
    coach: Coach = Depends(get_current_coach),
    db: AsyncSession = Depends(get_db),
):
    """获取当前教练的学员列表。"""
    rows = await get_my_students(db, coach.id)
    return success_response(msg="获取成功", data=_serialize(MyStudentItem, rows))


# ===== 19.4 授课记录 =====

@coach_panel_router.get("/records", summary="授课记录")
async def get_coach_records(
    coach: Coach = Depends(get_current_coach),
    db: AsyncSession = Depends(get_db),
):
    """获取当前教练的授课记录。"""
    rows = await get_my_records(db, coach)
    return success_response(msg="获取成功", data=_serialize(MyRecordItem, rows))


# ===== 19.5 训练计划列表 =====

@coach_panel_router.get("/plans", summary="训练计划列表")
async def list_coach_plans(
    coach: Coach = Depends(get_current_coach),
    db: AsyncSession = Depends(get_db),
):
    """19.5 训练计划列表（当前教练创建的）。"""
    plans = await list_my_plans(db, coach.id)
    items = [
        _plan_payload(plan, MemberBrief.model_validate(plan.member) if plan.member else None)
        for plan in plans
    ]
    return success_response(msg="获取成功", data=items)


# ===== 19.6 新增训练计划 =====

@coach_panel_router.post("/plans", summary="新增训练计划")
async def create_coach_plan(
    plan: PlanCreate,
    coach: Coach = Depends(get_current_coach),
    db: AsyncSession = Depends(get_db),
):
    """19.6 制定训练计划。"""
    member = await getOneMember(plan.member_id, db)
    if not member:
        raise BizError("会员不存在", code=MEMBER_NOT_FOUND, status_code=404)
    if plan.end_date < plan.start_date:
        raise BizError("结束日期不能早于开始日期", code=HTTP_BAD_REQUEST, status_code=400)

    created = await create_plan(db, coach.id, plan)
    await db.commit()
    return success_response(
        msg="制定成功",
        data=_plan_payload(created, MemberBrief(id=member.id, name=member.name)),
    )


# ===== 14.3 编辑训练计划 =====

@coach_panel_router.put("/plans/{plan_id}", summary="编辑训练计划")
async def update_coach_plan(
    plan_id: int,
    plan: PlanUpdate,
    coach: Coach = Depends(get_current_coach),
    db: AsyncSession = Depends(get_db),
):
    """14.3 编辑训练计划（只能改自己创建的计划）。"""
    updated = await update_plan(db, plan_id, coach.id, plan)
    if not updated:
        raise BizError("计划不存在", code=HTTP_NOT_FOUND, status_code=404)
    if updated.end_date < updated.start_date:
        raise BizError("结束日期不能早于开始日期", code=HTTP_BAD_REQUEST, status_code=400)

    await db.commit()
    return success_response(
        msg="编辑成功",
        data=_plan_payload(updated, await _member_brief(db, updated.member_id)),
    )
