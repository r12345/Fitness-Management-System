"""训练计划、打卡与运动记录接口。"""
from typing import Optional

from fastapi import Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .router import training_router
from ...core.database import get_db
from ...core.security import get_current_user
from ...crud.training import (
    create_checkin, leave_checkin, list_my_checkins,
    create_exercise_record, list_exercise_records, get_training_statistics,
)
from ...models import Member, User
from ...schemas.training import (
    CheckinCreate, LeaveCheckin, ExerciseRecordCreate, CheckinItem, ExerciseRecordItem,
)
from ...utils.res import success_response


async def _get_current_member(db: AsyncSession, user: User) -> Member:
    member = await db.scalar(select(Member).where(Member.user_id == user.id))
    if not member:
        raise HTTPException(status_code=404, detail="未找到会员档案")
    return member


@training_router.post('/checkin')
async def create_checkin_api(
    data: CheckinCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """13.1 到店打卡。"""
    member = await _get_current_member(db, user)
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
    member = await _get_current_member(db, user)
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
    member = await _get_current_member(db, user)
    records = await list_my_checkins(db, member.id)
    return success_response(data=[CheckinItem.model_validate(r).model_dump(mode="json") for r in records])


@training_router.post('/records')
async def create_record_api(
    data: ExerciseRecordCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """13.4 新增运动记录。"""
    record = await create_exercise_record(db, data)
    await db.commit()
    await db.refresh(record)
    return success_response(msg="新增成功", data=ExerciseRecordItem.model_validate(record).model_dump(mode="json"))


@training_router.get('/records')
async def list_records_api(
    member_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """13.5 运动记录列表。"""
    records = await list_exercise_records(db, member_id)
    return success_response(data=[ExerciseRecordItem.model_validate(r).model_dump(mode="json") for r in records])


@training_router.get('/statistics')
async def get_statistics_api(
    period: str = Query(..., pattern="^(week|month)$"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """13.6 训练统计。"""
    member = await _get_current_member(db, user)
    stats = await get_training_statistics(db, member.id, period)
    return success_response(data=stats)
