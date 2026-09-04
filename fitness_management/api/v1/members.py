"""会员管理与消费记录接口。"""
from decimal import Decimal
from typing import Optional

from fastapi import Depends, Query , HTTPException

from fitness_management.api.v1.router import members_router
from fitness_management.core.database import get_db
from fitness_management.core.security import get_current_user
from fitness_management.crud.member import show_all_members, add_member, delete_member, renew_card, getDetailMember, \
    getOneMember, get_total, updateMember, updateMemberStatus
from fitness_management.models import User
from fitness_management.schemas.member import MemberRequest, RenewMember, MemberStatus
from fitness_management.utils.res import success_response


@members_router.post("/")
async def create_member(member:MemberRequest,db=Depends(get_db),user:User=Depends(get_current_user)):
    member = await add_member(member, db)
    if member:
        return success_response()
    return {"message":"创建失败"}



@members_router.get("/")
async def get_members(db=Depends(get_db),
page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页条数"),
    keyword: Optional[str] = Query(None, description="课程名称或教练"),
    status: Optional[str] = Query(None, description="已上架/已下架"),
                      card_type: Optional[str] = Query(None, description="group / private"),
                      user:User=Depends(get_current_user)):
    members,total = await show_all_members(page,page_size,keyword,status,card_type,db)

    data={
        "items":members,
        'total':total,
        'page':page,
        'page_size':page_size,
        'total_pages':total//page_size+1

    }
    return success_response(data=data)



@members_router.delete("/{id}")
async def destroy_member(id:int,db=Depends(get_db),user:User=Depends(get_current_user)):
    flag=await delete_member(id,db)
    if flag:
        return success_response(msg='删除成功')
    return {"message":"删除失败"}

@members_router.put("/{id}/renew")
async def create_card(id:int,renew_info:RenewMember,db=Depends(get_db),user:User=Depends(get_current_user)):
    instance = await renew_card(id, renew_info, db,user)
    if instance is not None:
        return success_response(msg='续卡成功',data={
            'member_id':id,
            'new_expire':instance[0].card_expire,
            'balance':instance[0].balance,
            'consumption':instance[1].id
        })
    else:
        raise HTTPException(status_code=404,detail='续卡失败,没有该用户或金额小于0')

@members_router.get("/{id}")
async def get_member_detail(id:int,db=Depends(get_db)):
    member = await getOneMember(id, db)
    if member:
        records,appointments,checkins = await getDetailMember(member.id, db)
        return success_response(data={
            'items':member,
            "consumptions":[record for record in records],
            'appointments':[a for a in appointments],
            'checkins':[c for c in checkins]
        })
    else:
        raise HTTPException(status_code=404, detail="会员不存在")


@members_router.put('/{id}')
async def update_member(id:int,member:MemberRequest,db=Depends(get_db),user:User=Depends(get_current_user)):
    flag = await updateMember(id,member,db)
    if flag:
        return success_response(msg='更新成功')
    else:
        return {'code':1,"message":"更新失败"}


@members_router.put('/{id}/status')
async def update_member_status(id:int,status:MemberStatus,db=Depends(get_db),user: User = Depends(get_current_user)):
    flag = await updateMemberStatus(id,status,db)
    if flag:
        return success_response(msg='更新成功')
    else:
        return {'code': 1, "message": "更新失败"}


