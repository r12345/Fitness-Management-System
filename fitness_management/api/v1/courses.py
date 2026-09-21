"""课程管理接口。"""
from typing import Optional

from fastapi import Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from .router import courses_router
from fitness_management.core.database import get_db
from fitness_management.core.security import require_roles
from fitness_management.crud import course as course_crud
from fitness_management.crud.coach import current_coach_id_if_coach
from fitness_management.crud.coach_panel import list_upcoming_schedules
from fitness_management.crud.member import get_member_by_user
from fitness_management.models import User
from fitness_management.schemas.course import (
    CourseCreate,
    CourseUpdate,
    CourseToggle,
    CourseListItem,
    AppointmentItem,
)
from fitness_management.utils.res import success_response


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
    user: User = Depends(require_roles("admin", "reception", "coach", "member")),
):
    courses, total = await course_crud.list_courses(
        db, page, page_size, keyword, course_type, category, status, coach_id
    )
    # 计算每个课程的 booked_count
    result_items = []
    for c in courses:
        booked = await course_crud.get_booked_count(db, c.id)
        result_items.append(CourseListItem.from_course(c, booked))

    total_pages = (total + page_size - 1) // page_size if total else 0
    return success_response(data={
        "items": result_items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    })


# ===== 11.1b 上课地点候选 =====

@courses_router.get("/locations")
async def list_course_locations(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles("admin", "reception", "coach")),
):
    """「新增/编辑课程」地点输入框的 datalist 数据源。

    取课程表与排课表里出现过的教室名。地点仍然允许手输（可能新开教室），
    这里只是把馆里已有叫法给出来，避免同一个教室写成两种名字。
    教练改排课时也用这个接口，所以对 coach 同样放行。
    """
    return success_response(data=await course_crud.list_course_locations(db))


# ===== 11.7 全部教练排课（会员预约用）=====

@courses_router.get("/schedules")
async def list_course_schedules(
    course_type: Optional[str] = Query(None, description="group / private"),
    keyword: Optional[str] = Query(None, description="课程名称或教练"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles("admin", "reception", "coach", "member")),
):
    """馆内**所有教练**在排课窗口内的课，供「预约课程」页按排课下单。

    会员约的不该是课程表里那个「每周一次」的时间模板（它的日期可能是过去某个时间点），
    而是教练排出来的**具体某一次课**：带上日期与时段，预约才能落到那一条排课上，
    之后教练改时间/地点，会员的预约也跟着更新。

    四个角色都放行：管理员/前台/教练看的是同一份课表，权限差异在写操作上。
    """
    # 会员带上本人档案，列表会标出「这一节我已约过」；其余角色没有会员档案，
    # 传 None（不查库，免得给教练/管理员抛 404）——与 appointments.py 的写法一致。
    member_id = (await get_member_by_user(db, user)).id if user.role == "member" else None
    return success_response(
        data=await list_upcoming_schedules(
            db, course_type=course_type, keyword=keyword, member_id=member_id
        )
    )


# ===== 11.2 新增课程 =====

@courses_router.post("/", status_code=201)
async def create_course(
    data: CourseCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles("admin", "reception", "coach")),
):
    # 教练建课归属强制是自己；管理员/前台不限（None，以请求体为准）
    owner_coach_id = await current_coach_id_if_coach(db, user)
    effective_coach_id = owner_coach_id if owner_coach_id is not None else data.coach_id

    # 校验教练存在 —— 校验的是**最终归属**那个教练。
    # 原先校验的是请求体里的 coach_id：教练传了别人的编号会被报「教练不存在」，
    # 但真正落库的是他自己，文案与事实不符。
    from fitness_management.models.coach import Coach
    from sqlalchemy import select as sa_select
    coach = (await db.execute(
        sa_select(Coach).where(Coach.id == effective_coach_id)
    )).scalar_one_or_none()
    if not coach:
        raise HTTPException(status_code=400, detail="教练不存在")

    course = await course_crud.create_course(db, data, owner_coach_id=owner_coach_id)
    await db.commit()
    booked = await course_crud.get_booked_count(db, course.id)
    return success_response(msg="新增成功", data=CourseListItem.from_course(course, booked))


# ===== 11.3 编辑课程 =====

@courses_router.put("/{course_id}")
async def update_course(
    course_id: int,
    data: CourseUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles("admin", "reception", "coach")),
):
    owner_coach_id = await current_coach_id_if_coach(db, user)
    course = await course_crud.update_course(db, course_id, data, owner_coach_id=owner_coach_id)
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在")
    await db.commit()
    booked = await course_crud.get_booked_count(db, course.id)
    return success_response(msg="更新成功", data=CourseListItem.from_course(course, booked))


# ===== 11.4 删除课程 =====

@courses_router.delete("/{course_id}")
async def delete_course(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles("admin", "reception", "coach")),
):
    # 校验课程存在
    course = await course_crud.get_course(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在")

    # 先判归属再谈能不能删：不是自己名下的课，直接 403，
    # 别让人从「该课程存在 N 条预约」里读出别人课程的预约量
    owner_coach_id = await current_coach_id_if_coach(db, user)
    course_crud.ensure_course_owner(course, owner_coach_id)

    # 校验无进行中的预约
    booked = await course_crud.get_booked_count(db, course_id)
    if booked > 0:
        raise HTTPException(status_code=400, detail=f"该课程存在 {booked} 条预约，无法删除")

    ok = await course_crud.delete_course(db, course_id, owner_coach_id=owner_coach_id)
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
    user: User = Depends(require_roles("admin", "reception", "coach")),
):
    if data.status not in ("已上架", "已下架"):
        raise HTTPException(status_code=400, detail="状态值只能是 已上架 或 已下架")
    owner_coach_id = await current_coach_id_if_coach(db, user)
    course = await course_crud.toggle_course(db, course_id, data.status, owner_coach_id=owner_coach_id)
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在")
    await db.commit()
    booked = await course_crud.get_booked_count(db, course.id)
    return success_response(msg="上下架成功", data=CourseListItem.from_course(course, booked))


# ===== 11.6 课程预约名单 =====

@courses_router.get("/{course_id}/appointments")
async def get_course_appointments(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles("admin", "reception", "coach")),
):
    course = await course_crud.get_course(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在")

    appointments = await course_crud.get_course_appointments(db, course_id)
    items = [AppointmentItem.from_appointment(a) for a in appointments]
    return success_response(data={"items": items, "total": len(items)})
