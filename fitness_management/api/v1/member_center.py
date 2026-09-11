"""会员个人中心接口。"""
from fastapi import Depends, HTTPException

from fitness_management.api.v1.router import member_center_router
from fitness_management.core.database import get_db
from fitness_management.core.security import get_current_user
from fitness_management.crud.member_center import get_member_info_by_id, get_appointment_by_id, get_courses_by_id, \
    edit_my_profile
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


@member_center_router.put('/profile')
async def update_my_profile(member_info:MemberCenterRequest,user: User = Depends(get_current_user),db=Depends(get_db)):
    """会员个人中心接口。"""
    member = await get_member_info_by_id(user.id, db)
    if member is None:
        raise HTTPException(status_code=404, detail="会员不存在")
    member = await edit_my_profile(member_info,member, db)
    return success_response(data=member)

