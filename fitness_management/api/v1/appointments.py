"""课程预约、取消与签到接口。"""
from datetime import date as date_type
from typing import Optional

from fastapi import Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from .router import appointments_router
from fitness_management.core.database import get_db
from fitness_management.core.security import get_current_user, require_roles
from fitness_management.crud.appointment import (
    cancel_appointment,
    checkin_appointment,
    create_appointment,
    list_appointments,
    resolve_appointment,
)
from fitness_management.crud.member import get_member_by_user
from fitness_management.models import User
from fitness_management.schemas.appointment import AppointmentCreate, AppointmentResolve
from fitness_management.utils.res import success_response


# ===== 12.1 预约分页列表 =====

@appointments_router.get("")
async def list_appointments_api(
    keyword: Optional[str] = Query(None, description="关键词：会员姓名/课程名称/教练姓名"),
    status: Optional[str] = Query(None, description="预约状态：已预约/已签到/已完成/已取消"),
    date_: Optional[date_type] = Query(None, alias="date", description="预约日期"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页条数"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # 会员只能看到本人的预约，其余角色可查看全部
    member_id = (await get_member_by_user(db, user)).id if user.role == "member" else None

    items, total = await list_appointments(
        db,
        page=page,
        page_size=page_size,
        keyword=keyword,
        status=status,
        date_=date_,
        member_id=member_id,
    )
    return success_response(data={
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    })


# ===== 12.2 会员预约课程 =====

@appointments_router.post("")
async def create_appointment_api(
    data: AppointmentCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # 会员角色强制使用本人的会员编号，不信任请求体里的 member_id
    member_id = (await get_member_by_user(db, user)).id if user.role == "member" else None

    appointment, member, course = await create_appointment(db, data, member_id=member_id)
    await db.commit()
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

@appointments_router.delete("/{appointment_id}")
async def cancel_appointment_api(
    appointment_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # 取消后释放课程名额，会员只能取消本人的预约
    member_id = (await get_member_by_user(db, user)).id if user.role == "member" else None

    appointment = await cancel_appointment(db, appointment_id, member_id=member_id)
    await db.commit()
    return success_response(
        msg="取消成功",
        data={"appointment_id": appointment.id, "status": appointment.status},
    )


# ===== 12.4 预约签到 =====

@appointments_router.post("/{appointment_id}/checkin")
async def checkin_appointment_api(
    appointment_id: int,
    db: AsyncSession = Depends(get_db),
    # 签到只有教练/前台/管理员能做；会员给自己签到也走不通（前端本来也不给这个按钮）
    user: User = Depends(require_roles("admin", "reception", "coach")),
):
    appointment = await checkin_appointment(db, appointment_id)
    await db.commit()
    return success_response(
        msg="签到成功",
        data={"appointment_id": appointment.id, "status": appointment.status},
    )


# ===== 12.5 处理预约冲突 =====

@appointments_router.put("/{appointment_id}/resolve")
async def resolve_appointment_api(
    appointment_id: int,
    data: AppointmentResolve,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles("admin", "reception")),
):
    appointment = await resolve_appointment(
        db, appointment_id, target_status=data.status, remark=data.remark
    )
    await db.commit()
    return success_response(
        msg="处理成功",
        data={
            "appointment_id": appointment.id,
            "status": appointment.status,
            "remark": appointment.remark,
        },
    )
