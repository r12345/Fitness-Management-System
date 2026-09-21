"""会员管理与消费记录接口。"""
from typing import Optional

from fastapi import Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from fitness_management.api.v1.router import members_router
from fitness_management.core.database import get_db
from fitness_management.core.security import require_roles
from fitness_management.crud.member import show_all_members, add_member, delete_member, renew_card, getDetailMember, \
    getOneMember, updateMember, updateMemberStatus, sync_card_statuses
from fitness_management.crud.user import DEFAULT_PASSWORD
from fitness_management.models import User
from fitness_management.schemas.member import MemberRequest, RenewMember, MemberStatus
from fitness_management.utils.res import success_response


@members_router.post("/")
async def create_member(
    member: MemberRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles("admin", "reception")),
):
    """新增会员（开卡）。

    除了会员档案，还会开一个能登录的账号（账号 = 手机号，初始密码 123456）——
    否则办完卡的会员没有账号，进不了会员中心，自己也看不到打卡与预约。
    账号信息随响应返回，前台办卡时当面告知即可。
    """
    created, username = await add_member(member, db)
    if not created:
        raise HTTPException(status_code=400, detail="创建失败")
    return success_response(
        msg=f"创建成功，登录账号 {username}（初始密码 {DEFAULT_PASSWORD}）",
        data={
            "member_id": created.id,
            "name": created.name,
            "account": {
                "username": username,
                "password": DEFAULT_PASSWORD,
                "role": "member",
            },
        },
    )



@members_router.get("/")
async def get_members(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页条数"),
    keyword: Optional[str] = Query(None, description="会员姓名或手机号"),
    status: Optional[str] = Query(None, description="卡状态：正常/过期"),
    card_type: Optional[str] = Query(None, description="卡种：年卡/季卡/月卡/次卡"),
    user: User = Depends(require_roles("admin", "reception")),
):
    members,total = await show_all_members(page,page_size,keyword,status,card_type,db)

    data={
        "items":members,
        'total':total,
        'page':page,
        'page_size':page_size,
        # 原来是 total // page_size + 1：total=10、page_size=10 时算出来是 2 页（实际 1 页），
        # 整除的情况下永远多一页。统一用向上取整。
        'total_pages':(total + page_size - 1) // page_size if total else 0
    }
    return success_response(data=data)



@members_router.delete("/{id}")
async def destroy_member(
    id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles("admin", "reception")),
):
    flag=await delete_member(id,db)
    if flag:
        return success_response(msg='删除成功')
    raise HTTPException(status_code=404, detail="会员不存在")

@members_router.put("/{id}/renew")
async def create_card(
    id: int,
    renew_info: RenewMember,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles("admin", "reception")),
):
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
async def get_member_detail(
    id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles("admin", "reception")),
):
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
async def update_member(
    id: int,
    member: MemberRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles("admin", "reception")),
):
    flag = await updateMember(id,member,db)
    if flag:
        return success_response(msg='更新成功')
    raise HTTPException(status_code=404, detail="会员不存在")


@members_router.put('/{id}/status')
async def update_member_status(
    id: int,
    status: MemberStatus,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles("admin", "reception")),
):
    actual = await updateMemberStatus(id, status, db)
    if actual is None:
        raise HTTPException(status_code=404, detail="会员不存在")
    # 传「正常/过期」时会被到期时间归正，把实际生效的值告诉前端，避免页面显示与库不一致
    if actual != status.status:
        return success_response(msg=f'卡已到期，状态已归正为「{actual}」')
    return success_response(msg='更新成功')


@members_router.post('/sync-status')
async def sync_member_card_status(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles("admin", "reception")),
):
    """手动把全部会员卡状态按到期时间归正（列表/详情查询时也会自动执行）。"""
    fixed = await sync_card_statuses(db)
    return success_response(msg=f'已同步 {fixed} 张会员卡状态', data={'fixed': fixed})

