"""会员个人中心接口。"""
from fastapi import Depends, HTTPException

from fitness_management.api.v1.router import member_center_router
from fitness_management.core.database import get_db
from fitness_management.core.security import get_current_user
from fitness_management.crud.member_center import get_member_info_by_id, get_appointment_by_id, get_courses_by_id, \
    edit_my_profile
from fitness_management.crud.coach_panel import list_upcoming_schedules
from fitness_management.models import User
from fitness_management.schemas.member_center import MemberCenterRequest
from fitness_management.utils.res import success_response


@member_center_router.get('/')
async def get_member_info(user: User = Depends(get_current_user),db=Depends(get_db)):
    member = await get_member_info_by_id(user.id,db)
    if member is None:
        raise HTTPException(status_code=404, detail="会员不存在")
    return success_response(data=member)

@member_center_router.get('/appointments')
async def get_my_appointments(user: User = Depends(get_current_user),db=Depends(get_db)):
    member = await get_member_info_by_id(user.id,db)
    if member is None:
        raise HTTPException(status_code=404, detail="会员不存在")
    list = await get_appointment_by_id(member.id, db)
    return success_response(data=list)


@member_center_router.get('/courses')
async def get_my_courses(user: User = Depends(get_current_user),db=Depends(get_db)):
    """会员个人中心接口。"""
    member = await get_member_info_by_id(user.id, db)
    if member is None:
        raise HTTPException(status_code=404, detail="会员不存在")
    list = await get_courses_by_id(member.id, db)
    return success_response(data=list)


@member_center_router.get('/schedules')
async def get_upcoming_schedules(user: User = Depends(get_current_user),db=Depends(get_db)):
    """会员可预约的排课：全部教练、从今天起往后 4 周的排课。

    会员看到的不是「某个教练的课」，而是馆里所有教练在这段时间内的课，
    每条都带上课程、教练、上课日期、时间段、地点与状态，并且标了 can_book
    （状态为未开始且未约满才能约）。查之前会把窗口内的排课补齐并归正状态，
    新开的课程也能立刻出现在列表里。

    这里同样先取会员档案：本模块的接口都是「本人视角」，
    不取档案的话非会员账号打进来会拿到一份 200 的课表，与同文件其它接口的 404 口径不一致。
    档案的 id 还要传给查询，用来标出「这一节我已经约过了」。
    """
    member = await get_member_info_by_id(user.id, db)
    if member is None:
        raise HTTPException(status_code=404, detail="会员不存在")
    return success_response(data=await list_upcoming_schedules(db, member_id=member.id))


@member_center_router.put('/profile')
async def update_my_profile(member_info:MemberCenterRequest,user: User = Depends(get_current_user),db=Depends(get_db)):
    """会员个人中心接口。"""
    member = await get_member_info_by_id(user.id, db)
    if member is None:
        raise HTTPException(status_code=404, detail="会员不存在")
    member = await edit_my_profile(member_info,member, db)
    return success_response(data=member)

