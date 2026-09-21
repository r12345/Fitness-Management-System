"""前台运营工作台接口。"""
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from .router import reception_router
from ...core.database import get_db
from ...core.security import require_roles
from ...crud.reception import (
    get_sum, get_re_business_log, list_staff, create_staff, delete_staff, delete_staff_account,
)
from ...crud.user import DEFAULT_PASSWORD
from ...models import User
from ...schemas.reception import ReceptionCreate
from ...utils.res import success_response


@reception_router.get("/summary")
async def get_summary(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles("admin", "reception")),
):
    data = await get_sum(db)
    return success_response(data=data)

@reception_router.get("/business-log")
async def get_reception_business_log(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles("admin", "reception")),
):
    data = await get_re_business_log(db)
    return success_response(data=data)


# ===== 运营（前台）人员：账号由超级管理员统一开 =====
# 新增教练/会员同一套做法（见 api/v1/coaches.py 9.2、api/v1/members.py）
# 列表以「登录账号」为准（能否登进前台工作台才是实质），并集上人员档案，
# 免得历史遗留的「只注册过账号、没档案」的人在管理页面上消失。

@reception_router.get("/staff")
async def get_reception_staff(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles("admin")),
):
    """运营人员列表（仅管理员）。

    列表是「登录账号 ∪ 人员档案」：只有账号没档案的（历史遗留）也会列出来，
    不会再凭空消失。has_profile / has_account 两个标记告诉前端这一行长什么样。
    """
    return success_response(data=await list_staff(db))


@reception_router.post("/staff")
async def create_reception_staff(
    data: ReceptionCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles("admin")),
):
    """新增运营人员（仅管理员），同时保证有登录账号。

    手机号下已经有运营账号时（历史遗留的「只注册过、没建档」），
    直接认领那个账号补档案，不新建账号、也不重置它的密码。
    """
    staff, username, adopted = await create_staff(db, data)
    if adopted:
        msg = f"已为「{staff.name}」补建人员档案，沿用原登录账号 {username}（密码未改动）"
    else:
        msg = f"创建成功，登录账号 {username}（初始密码 {DEFAULT_PASSWORD}）"
    return success_response(
        msg=msg,
        data={
            "id": staff.id,
            "name": staff.name,
            # 认领已有账号时不能瞎报 123456 —— 那个账号的密码我们没碰过
            "account": {
                "username": username,
                "password": None if adopted else DEFAULT_PASSWORD,
                "role": "reception",
                "adopted": adopted,
            },
        },
    )


@reception_router.delete("/staff/{staff_id}")
async def remove_reception_staff(
    staff_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles("admin")),
):
    """删除运营人员（仅管理员），其登录账号一并删除。"""
    name = await delete_staff(db, staff_id)
    if name is None:
        raise HTTPException(status_code=404, detail="该运营人员不存在")
    return success_response(msg=f"已删除运营人员「{name}」，其登录账号同时删除")


@reception_router.delete("/staff/account/{user_id}")
async def remove_reception_account(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles("admin")),
):
    """删除一条还没建档案的运营账号（仅管理员）。

    列表里「未建档」那类行用它；已经有档案的会被 400 拦住，要走 /staff/{staff_id}，
    否则档案会变成没账号的孤儿。注意这条路由有三段路径，不会和 /staff/{staff_id} 撞。
    """
    username = await delete_staff_account(db, user_id)
    if username is None:
        raise HTTPException(status_code=404, detail="该运营账号不存在")
    return success_response(msg=f"已删除运营账号「{username}」")
