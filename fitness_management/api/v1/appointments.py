"""课程预约、取消与签到接口（接口文档 §12）。

    预约  会员对课程时段的预约
    签到  会员到店或上课时确认到场

路径前缀：``/api/v1/appointments``
"""
from datetime import date as date_type
from typing import Optional

from fastapi import Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .router import appointments_router
from ...core.database import get_db
from ...core.security import get_current_user
from ...crud.appointment import (
    cancel_appointment,
    checkin_appointment,
    create_appointment,
    list_appointments,
    resolve_appointment,
)
from ...models import Member, User
from ...schemas.appointment import AppointmentCreate, AppointmentPageResponse, AppointmentResolve
from ...utils.res import BizError, success_response


async def _get_current_member_id(db: AsyncSession, user: User) -> int:
    """取当前登录用户对应的会员编号（会员角色专用）。"""
    member = await db.scalar(select(Member).where(Member.user_id == user.id))
    if not member:
        raise BizError("未找到会员档案", code=2001, status_code=404)
    return member.id


# ===== 12.1 预约分页列表 =====

@appointments_router.get("", response_model=AppointmentPageResponse, summary="预约分页列表")
async def list_appointments_api(
    member_id: Optional[int] = Query(None, description="会员编号"),
    course_id: Optional[int] = Query(None, description="课程编号"),
    status: Optional[str] = Query(None, description="预约状态：已预约/已签到/已完成/已取消"),
    date_: Optional[date_type] = Query(None, alias="date", description="预约日期"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页条数"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """预约分页列表。

    管理员/前台/教练可查看全部；会员角色只能看到自己的预约。
    """
    if user.role == "member":
        member_id = await _get_current_member_id(db, user)

    items, total = await list_appointments(
        db=db,
        page=page,
        page_size=page_size,
        member_id=member_id,
        course_id=course_id,
        status=status,
        date_=date_,
    )
    return {
        "code": 0,
        "msg": "success",
        "data": {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        },
    }


# ===== 12.2 会员预约课程 =====

@appointments_router.post("", summary="会员预约课程")
async def create_appointment_api(
    data: AppointmentCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """会员预约课程。会员角色强制使用本人的会员编号。"""
    member_id = None
    if user.role == "member":
        member_id = await _get_current_member_id(db, user)

    appointment, member, course = await create_appointment(db, data, member_id=member_id)
    return success_response(
        msg="预约成功",
        data={
            "appointment_id": appointment.id,
            "member": member.name,
            "course": course.name,
            "status": appointment.status,
        },
    )


# ===== 12.3 取消预约 =====

@appointments_router.delete("/{appointment_id}", summary="取消预约")
async def cancel_appointment_api(
    appointment_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """取消预约，取消后释放课程名额。会员角色只能取消本人的预约。"""
    member_id = None
    if user.role == "member":
        member_id = await _get_current_member_id(db, user)

    appointment = await cancel_appointment(db, appointment_id, member_id=member_id)
    return success_response(
        msg="取消成功",
        data={"appointment_id": appointment.id, "status": appointment.status},
    )


# ===== 12.4 预约签到 =====

@appointments_router.post("/{appointment_id}/checkin", summary="预约签到")
async def checkin_appointment_api(
    appointment_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """预约签到（教练、前台运营）。"""
    appointment = await checkin_appointment(db, appointment_id)
    return success_response(
        msg="签到成功",
        data={"appointment_id": appointment.id, "status": appointment.status},
    )


# ===== 12.5 处理预约冲突 =====

@appointments_router.put("/{appointment_id}/resolve", summary="处理预约冲突")
async def resolve_appointment_api(
    appointment_id: int,
    data: AppointmentResolve,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """处理预约冲突：修正预约状态并记录备注。"""
    appointment = await resolve_appointment(
        db, appointment_id, target_status=data.status, remark=data.remark
    )
    return success_response(
        msg="处理成功",
        data={
            "appointment_id": appointment.id,
            "status": appointment.status,
            "remark": appointment.remark,
        },
    )
