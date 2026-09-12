"""课程管理接口。"""
from datetime import datetime
from typing import Optional

from fastapi import Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from .router import courses_router
from fitness_management.core.database import get_db
from fitness_management.core.security import get_current_user
from fitness_management.crud import course as course_crud
from fitness_management.models import User
from fitness_management.schemas.course import (
    CourseCreate,
    CourseUpdate,
    CourseToggle,
    CourseListItem,
    AppointmentItem,
)
from fitness_management.utils.res import success_response

# 星期映射
_WEEKDAYS = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


def _fmt_start_time(dt):
    # 兼容字符串：如果是字符串，先转成 datetime 对象
    if isinstance(dt, str):
        dt = datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
    return f"{_WEEKDAYS[dt.weekday()]} {dt.strftime('%H:%M')}"


def _to_course_list_item(course, booked_count: int) -> dict:
    """ORM Course → 列表项字典。"""
    return {
        "id": course.id,
        "name": course.name,
        "course_type": course.course_type,
        "category": course.category,
        "coach_id": course.coach_id,
        "coach_name": course.coach.name if course.coach else "",
        "start_time": _fmt_start_time(course.start_time),
        "duration": course.duration,
        "max_count": course.max_count,
        "booked_count": booked_count,
        "price": course.price,
        "status": course.status,
    }


# ===== 11.1 课程列表 =====

@courses_router.get("/")
async def list_courses(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页条数"),
    keyword: Optional[str] = Query(None, description="课程名称或教练"),
    course_type: Optional[str] = Query(None, description="group / private"),
    category: Optional[str] = Query(None, description="课程分类"),
    status: Optional[str] = Query(None, description="已上架/已下架"),
    coach_id: Optional[int] = Query(None, description="教练编号"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    courses, total = await course_crud.list_courses(
        db, page, page_size, keyword, course_type, category, status, coach_id
    )
    # 计算每个课程的 booked_count
    result_items = []
    for c in courses:
        booked = await course_crud.get_booked_count(db, c.id)
        result_items.append(_to_course_list_item(c, booked))

    total_pages = (total + page_size - 1) // page_size if total else 0
    return success_response(data={
        "items": result_items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    })


# ===== 11.2 新增课程 =====

@courses_router.post("/", status_code=201)
async def create_course(
    data: CourseCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # 校验教练存在
    from fitness_management.models.coach import Coach
    from sqlalchemy import select as sa_select
    coach = (await db.execute(sa_select(Coach).where(Coach.id == data.coach_id))).scalar_one_or_none()
    if not coach:
        raise HTTPException(status_code=400, detail="教练不存在")

    course = await course_crud.create_course(db, data)
    await db.commit()
    booked = await course_crud.get_booked_count(db, course.id)
    return success_response(msg="新增成功", data=_to_course_list_item(course, booked))


# ===== 11.3 编辑课程 =====

@courses_router.put("/{course_id}")
async def update_course(
    course_id: int,
    data: CourseUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    course = await course_crud.update_course(db, course_id, data)
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在")
    await db.commit()
    booked = await course_crud.get_booked_count(db, course.id)
    return success_response(msg="更新成功", data=_to_course_list_item(course, booked))


# ===== 11.4 删除课程 =====

@courses_router.delete("/{course_id}")
async def delete_course(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # 校验课程存在
    course = await course_crud.get_course(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在")

    # 校验无进行中的预约
    booked = await course_crud.get_booked_count(db, course_id)
    if booked > 0:
        raise HTTPException(status_code=400, detail=f"该课程存在 {booked} 条预约，无法删除")

    ok = await course_crud.delete_course(db, course_id)
    await db.commit()
    if not ok:
        raise HTTPException(status_code=404, detail="课程不存在")
    return success_response(msg="删除成功", data=None)


# ===== 11.5 课程上下架 =====

@courses_router.post("/{course_id}/toggle")
async def toggle_course(
    course_id: int,
    data: CourseToggle,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if data.status not in ("已上架", "已下架"):
        raise HTTPException(status_code=400, detail="状态值只能是 已上架 或 已下架")
    course = await course_crud.toggle_course(db, course_id, data.status)
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在")
    await db.commit()
    booked = await course_crud.get_booked_count(db, course.id)
    return success_response(msg="上下架成功", data=_to_course_list_item(course, booked))


# ===== 11.6 课程预约名单 =====

@courses_router.get("/{course_id}/appointments")
async def get_course_appointments(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    course = await course_crud.get_course(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在")

    appointments = await course_crud.get_course_appointments(db, course_id)
    items = [
        {
            "member_id": a.member_id,
            "member": a.member.name if a.member else "",
            "phone": a.member.phone if a.member else "",
            "appointment_time": a.appointment_time,
            "status": a.status,
            "checked_in": a.checked_in,
        }
        for a in appointments
    ]
    return success_response(data={"items": items, "total": len(items)})
