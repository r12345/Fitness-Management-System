"""训练计划、打卡与运动记录接口。"""
from typing import Optional

from fastapi import Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from .router import training_router
from ...core.database import get_db
from ...core.security import get_current_user
from ...crud.member import get_member_by_user
from ...crud.training import (
    create_checkin, leave_checkin, list_my_checkins, get_open_checkin,
    create_exercise_record, list_exercise_records, get_training_statistics,
)
from ...models import User
from ...schemas.common import serialize_rows, to_payload
from ...schemas.training import (
    CheckinCreate, LeaveCheckin, ExerciseRecordCreate, CheckinItem, CurrentCheckin,
    ExerciseRecordItem,
)
from ...utils.res import success_response


@training_router.post('/checkin')
async def create_checkin_api(
    data: CheckinCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """13.1 到店打卡。"""
    member = await get_member_by_user(db, user)
    record = await create_checkin(db, member.id, data)
    await db.commit()
    return success_response(msg="打卡成功", data={
        "checkin_id": record.id,
        "checkin_time": data.checkin_time.strftime("%Y-%m-%d %H:%M:%S"),
    })


@training_router.put('/checkin/{checkin_id}/leave')
async def leave_checkin_api(
    checkin_id: int,
    data: LeaveCheckin,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """13.2 离开打卡。"""
    member = await get_member_by_user(db, user)
    record = await leave_checkin(db, checkin_id, member.id, data)
    if not record:
        raise HTTPException(status_code=404, detail="打卡记录不存在")
    await db.commit()
    return success_response(msg="离开打卡成功", data={
        "checkin_id": record.id,
        "leave_time": data.leave_time.strftime("%Y-%m-%d %H:%M:%S"),
        "duration": record.duration,
    })


@training_router.get('/checkin')
async def list_my_checkins_api(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """13.3 我的打卡记录。"""
    member = await get_member_by_user(db, user)
    records = await list_my_checkins(db, member.id)
    return success_response(data=serialize_rows(CheckinItem, records))


@training_router.post('/records')
async def create_record_api(
    data: ExerciseRecordCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """13.4 新增运动记录。"""
    # 会员角色强制写到自己名下：原来请求体里的 member_id 直接落库，
    # 任何登录用户都能给别的会员塞一条运动记录。
    if user.role == "member":
        member = await get_member_by_user(db, user)
        data = data.model_copy(update={"member_id": member.id})
    record = await create_exercise_record(db, data)
    await db.commit()
    await db.refresh(record)
    return success_response(msg="新增成功", data=to_payload(ExerciseRecordItem.model_validate(record)))


@training_router.get('/records')
async def list_records_api(
    member_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """13.5 运动记录列表。"""
    # 会员只返回本人记录。原来 member_id 原样透传，而会员端根本不传这个参数，
    # 于是 list_exercise_records(None) 把**全库**的运动记录都返回给了会员
    # —— 既越权看到了别人的数据，页面上也混进了别人的记录。
    if user.role == "member":
        member = await get_member_by_user(db, user)
        member_id = member.id
    records = await list_exercise_records(db, member_id)
    return success_response(data=serialize_rows(ExerciseRecordItem, records))


@training_router.get('/statistics')
async def get_statistics_api(
    period: str = Query(..., pattern="^(week|month)$"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """13.6 训练统计。"""
    member = await get_member_by_user(db, user)
    stats = await get_training_statistics(db, member.id, period)
    return success_response(data=stats)


@training_router.get('/checkin/current')
async def get_current_checkin_api(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """13.7 当前在店状态。

    前端刷新后用它恢复「到店打卡 / 离店打卡」按钮：只要库里还有一条未离店的
    记录就仍然是「已到店」，只有走完离店打卡才会变回「未到店」。
    """
    member = await get_member_by_user(db, user)
    record = await get_open_checkin(db, member.id)
    if not record:
        return success_response(data=to_payload(CurrentCheckin(checked_in=False)))
    return success_response(data=to_payload(CurrentCheckin(
        checked_in=True,
        checkin_id=record.id,
        checkin_date=record.checkin_date,
        checkin_time=record.checkin_time,
    )))
