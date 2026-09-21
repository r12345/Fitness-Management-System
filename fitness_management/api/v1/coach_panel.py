"""教练工作台接口。"""
from datetime import date as date_type
from typing import Optional

from fastapi import Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from .router import coach_panel_router
from fitness_management.core.database import get_db
from fitness_management.core.security import get_current_coach
from fitness_management.crud.coach import update_my_profile
from fitness_management.crud.coach_panel import (
    get_member_brief,
    get_my_records,
    get_my_schedules,
    get_my_students,
    list_assignable_members,
    list_plan_presets,
    schedule_window,
    update_my_schedule,
    update_my_schedule_status,
)
from fitness_management.crud.member import assign_student, getOneMember
from fitness_management.crud.training import create_plan, list_my_plans, update_plan
from fitness_management.models import Coach
from fitness_management.schemas.coach_panel import (
    MyPlanItem,
    MyProfileItem,
    MyProfileUpdate,
    MyRecordItem,
    MyScheduleItem,
    MyStudentItem,
    ScheduleStatusUpdate,
    ScheduleUpdate,
)
from fitness_management.schemas.common import serialize_rows, to_payload
from fitness_management.schemas.member import StudentAssign
from fitness_management.schemas.training import PlanCreate, PlanUpdate
from fitness_management.utils.res import success_response


# ===== 19.1 我的排课 =====

@coach_panel_router.get("/schedules")
async def get_coach_schedules(
    status: Optional[str] = Query(None, description="排课状态"),
    schedule_date: Optional[date_type] = Query(None, description="上课日期"),
    coach: Coach = Depends(get_current_coach),
    db: AsyncSession = Depends(get_db),
):
    """教练的排课由课程时间派生，这里只返回「今天前后各 2 周」的窗口。

    status 已按当前时间归正：未开始 / 进行中 / 已结束 / 已签到 / 已取消。
    """
    rows = await get_my_schedules(db, coach.id, status=status, schedule_date=schedule_date)
    return success_response(data=serialize_rows(MyScheduleItem, rows))


# ===== 19.1b 排课窗口 =====

@coach_panel_router.get("/schedules/window")
async def get_schedule_window(
    coach: Coach = Depends(get_current_coach),
):
    """当前排课窗口的起止日期。

    窗口天数（SCHEDULE_WINDOW_WEEKS）只写在后端一处，前端拿它显示「本周期的排课」，
    不在两边各算一遍 —— 否则改天数时必然有一边漏改。
    """
    start, end = schedule_window()
    return success_response(data={"start": start, "end": end})


# ===== 19.1c 训练计划预设候选值（新增/编辑计划输入框的 datalist 数据源）=====

@coach_panel_router.get("/plan-presets")
async def list_plan_preset_options(
    coach: Coach = Depends(get_current_coach),
    db: AsyncSession = Depends(get_db),
):
    """返回 {字段名: [候选值...]}。

    这些字段仍然允许自由输入（真实训练内容无法穷举），
    这里只是给教练一份常用值，省得每次从零打字、也统一了写法。
    """
    return success_response(data=await list_plan_presets(db))


# ===== 19.2 修改排课（日期 / 开始时间 / 结束时间 / 地点，并同步名下预约的时间）=====

@coach_panel_router.put("/schedules/{schedule_id}")
async def update_coach_schedule(
    schedule_id: int,
    data: ScheduleUpdate,
    coach: Coach = Depends(get_current_coach),
    db: AsyncSession = Depends(get_db),
):
    """排课不再手工新增 —— 课程一建就按课程时间把窗口内的课排好。

    这里改的是「这一次课挪到哪天、几点上、在哪上」；课程归属不可改，
    状态也不在这里改（走 /schedules/{id}/status）。

    改期会连带同步名下已预约的会员：他们的预约时间跟着这次课一起挪，
    所以预约管理与会员的预约课程两端看到的都是新时间。
    """
    schedule, synced = await update_my_schedule(db, schedule_id, coach.id, data)
    await db.commit()
    # 有多少条预约被一起挪了时间，明确回给前端 —— 否则教练只看到自己的课表变了，
    # 不知道已经报名的会员那边也跟着变了
    msg = "排课已修改"
    if synced:
        msg = f"排课已修改，{synced} 条预约的上课时间已同步"
    return success_response(
        msg=msg,
        data={
            "schedule_id": schedule.id,
            "schedule_date": schedule.schedule_date,
            "start_time": schedule.start_time,
            "end_time": schedule.end_time,
            "location": schedule.location,
            "status": schedule.status,
            "synced_appointments": synced,
        },
    )


# ===== 19.7 修改排课状态 =====

@coach_panel_router.put("/schedules/{schedule_id}/status")
async def update_coach_schedule_status(
    schedule_id: int,
    data: ScheduleStatusUpdate,
    coach: Coach = Depends(get_current_coach),
    db: AsyncSession = Depends(get_db),
):
    """签到 / 撤销签到 / 取消排课。

    签到（status=已签到）只在课程时段内有效：没到点提示「还没开始」、
    已下课提示「不能补签」，由服务端时间判定，前端按钮只是提示。
    撤销签到与恢复正常不受时间限制 —— 那是纠错动作。
    """
    schedule = await update_my_schedule_status(db, schedule_id, coach.id, data.status)
    await db.commit()
    return success_response(
        msg="状态修改成功",
        data={"schedule_id": schedule.id, "status": schedule.status},
    )


# ===== 19.3 我的学员 =====

@coach_panel_router.get("/students")
async def get_coach_students(
    coach: Coach = Depends(get_current_coach),
    db: AsyncSession = Depends(get_db),
):
    rows = await get_my_students(db, coach.id)
    return success_response(data=serialize_rows(MyStudentItem, rows))


# ===== 19.3b 新增学员（认领已有会员）=====

@coach_panel_router.post("/students")
async def create_coach_student(
    data: StudentAssign,
    coach: Coach = Depends(get_current_coach),
    db: AsyncSession = Depends(get_db),
):
    """教练新增学员：把一名**已有会员**挂到自己名下。

    会员档案来自前台开卡或本人注册，都已经带登录账号；
    教练只做「认领」，不新建会员 —— 以前这里的表单会现造一条 member，
    造出来的人没有账号，登不进会员中心，也查不到自己的打卡与预约。
    """
    member = await assign_student(coach.id, data.member_id, db)
    if member is None:
        raise HTTPException(status_code=404, detail="会员不存在")
    return success_response(msg=f"已添加学员「{member.name}」", data={
        "member_id": member.id,
        "name": member.name,
        "phone": member.phone,
        "card_type": member.card_type,
        "card_expire": member.card_expire,
        "status": member.status,
    })


# ===== 19.3c 新增学员下拉框：可认领的会员 =====

@coach_panel_router.get("/member-options")
async def list_member_options(
    keyword: Optional[str] = Query(None, description="会员姓名或手机号"),
    coach: Coach = Depends(get_current_coach),
    db: AsyncSession = Depends(get_db),
):
    """「新增学员」下拉框的候选会员（未分配 + 已经归属自己的）。

    下拉框的选项直接来自数据库里的会员姓名，教练不用手打名字，
    也就不会再造出「同一个人的两条档案」。
    """
    rows = await list_assignable_members(db, coach.id, keyword=keyword)
    return success_response(data=serialize_rows(MyStudentItem, rows))


# ===== 19.4 授课记录 =====

@coach_panel_router.get("/records")
async def get_coach_records(
    coach: Coach = Depends(get_current_coach),
    db: AsyncSession = Depends(get_db),
):
    rows = await get_my_records(db, coach)
    return success_response(data=serialize_rows(MyRecordItem, rows))


# ===== 19.5 训练计划列表 =====

@coach_panel_router.get("/plans")
async def list_coach_plans(
    coach: Coach = Depends(get_current_coach),
    db: AsyncSession = Depends(get_db),
):
    plans = await list_my_plans(db, coach.id)
    items = [MyPlanItem.from_plan(plan, plan.member) for plan in plans]
    return success_response(data=items)


# ===== 19.6 新增训练计划 =====

@coach_panel_router.post("/plans")
async def create_coach_plan(
    plan: PlanCreate,
    coach: Coach = Depends(get_current_coach),
    db: AsyncSession = Depends(get_db),
):
    member = await getOneMember(plan.member_id, db)
    if not member:
        raise HTTPException(status_code=404, detail="会员不存在")
    if plan.end_date < plan.start_date:
        raise HTTPException(status_code=400, detail="结束日期不能早于开始日期")

    created = await create_plan(db, coach.id, plan)
    await db.commit()
    return success_response(
        msg="制定成功",
        data=MyPlanItem.from_plan(created, member),
    )


# ===== 14.3 编辑训练计划 =====

@coach_panel_router.put("/plans/{plan_id}")
async def update_coach_plan(
    plan_id: int,
    plan: PlanUpdate,
    coach: Coach = Depends(get_current_coach),
    db: AsyncSession = Depends(get_db),
):
    updated = await update_plan(db, plan_id, coach.id, plan)
    if not updated:
        raise HTTPException(status_code=404, detail="计划不存在")
    if updated.end_date < updated.start_date:
        raise HTTPException(status_code=400, detail="结束日期不能早于开始日期")

    await db.commit()
    return success_response(
        msg="编辑成功",
        data=MyPlanItem.from_plan(updated, await get_member_brief(db, updated.member_id)),
    )


# ===== 19.8 我的资料（查看）=====

@coach_panel_router.get("/profile")
async def get_my_profile(
    coach: Coach = Depends(get_current_coach),
):
    """教练查看自己的档案。

    四个身份里只有教练原先没有任何「自助」入口：改手机号、改专长都得找管理员，
    而会员在自己的个人中心能改资料。这里补上读 + 写两个接口（写见 19.9）。
    """
    return success_response(data=to_payload(MyProfileItem.model_validate(coach)))


# ===== 19.9 我的资料（修改）=====

@coach_panel_router.put("/profile")
async def update_my_profile_api(
    data: MyProfileUpdate,
    coach: Coach = Depends(get_current_coach),
    db: AsyncSession = Depends(get_db),
):
    """教练自助修改个人资料：姓名 / 联系方式 / 专长。

    薪资、在职状态、累计课时、平均评分都不在请求体里（见 MyProfileUpdate），
    更不会在这里落库 —— 那些是管理员或系统统计维护的字段。
    """
    updated = await update_my_profile(db, coach, data)
    return success_response(
        msg="资料已更新",
        data=to_payload(MyProfileItem.model_validate(updated)),
    )
