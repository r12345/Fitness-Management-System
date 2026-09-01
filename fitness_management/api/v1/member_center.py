"""会员个人中心接口。"""
from fastapi import Depends

from fitness_management.api.v1.router import member_center_router
from fitness_management.core.database import get_db
from fitness_management.core.security import get_current_user
from fitness_management.crud.member_center import get_member_info_by_id
from fitness_management.models import User
from fitness_management.utils.res import success_response


@member_center_router.get('/')
async def member_center(user: User = Depends(get_current_user),db=Depends(get_db)):
    member = await get_member_info_by_id(user.id,db)
    if member:
        return success_response(data=member)
    else:
        return success_response(msg='失败',data=None)


@member_center_router.post('/member_center/{id}')
async def member_center(id: int, ):
    """会员个人中心接口。"""
    return {"id": id, "name": "member_center"}


@member_center_router.put('/member_center/{id}')
async def member_center(id: int, ):
    """会员个人中心接口。"""
    return {"id": id, "name": "member_center"}


@member_center_router.delete('/member_center/{id}')
async def member_center(id:int):
    pass
