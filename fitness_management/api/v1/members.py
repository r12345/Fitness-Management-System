"""会员管理与消费记录接口。"""
from decimal import Decimal

from fastapi import Depends

from fitness_management.api.v1.router import members_router
from fitness_management.core.database import get_db
from fitness_management.crud.member import show_all_members, add_member, delete_member, renew_card
from fitness_management.schemas.member import MemberRequest
from fitness_management.utils.res import success_response


@members_router.post("/")
async def create_member(member:MemberRequest,db=Depends(get_db)):
    member = await add_member(member, db)
    if member:
        return success_response()
    return {"message":"创建失败"}



@members_router.get("/")
async def get_members(db=Depends(get_db)):
    members = await show_all_members(db)
    return success_response(data=members)



@members_router.delete("/{id}")
async def destroy_member(id:int,db=Depends(get_db)):
    flag=await delete_member(id,db)
    if flag:
        return success_response(msg='删除成功')
    return {"message":"删除失败"}

@members_router.put("/{id}/renew")
async def create_card(member_id:int,renew:float,db=Depends(get_db)):
    renew = Decimal(str(renew))
    flag = await renew_card(member_id, renew, db)
    if flag:
        return success_response(msg='续卡成功')
    else:
        return {'code':1,"message":"续卡失败"}

