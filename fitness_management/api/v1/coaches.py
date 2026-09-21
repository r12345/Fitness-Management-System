"""教练管理、排班与授课统计接口。"""
from typing import Optional

from fastapi import Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...core.security import require_roles
from ...models import User
from ...schemas.coach import CoachCreate, CoachItem, CoachUpdate
from ...crud.coach import get_coach_page_list, create_coach_obj, update_coach_obj, delete_coach_obj, \
    get_coach_statistics_obj
from ...crud.user import DEFAULT_PASSWORD
from ...utils.res import success_response
from .router import coaches_router


# 路径不带尾斜杠：前端 api/coach.js 打的是 /coaches（POST）与 /coaches/（GET），
# 声明成 "/" 会让 POST 每次都吃一个 307 重定向，这里统一为不带斜杠。


# ===== 9.1 教练分页列表 =====

@coaches_router.get("")
async def list_coaches(
    keyword: Optional[str] = Query(None, description="姓名或手机号"),
    status: Optional[str] = Query(None, description="在职/休假/离职"),
    specialty: Optional[str] = Query(None, description="专长关键词"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    # 教练列表是「课程管理」里选授课教练的下拉框数据源，教练自己也要读
    user: User = Depends(require_roles("admin", "reception", "coach")),
):
    """教练分页列表。"""
    page_data = await get_coach_page_list(
        db=db,
        keyword=keyword,
        status=status,
        specialty=specialty,
        page=page,
        page_size=page_size
    )
    return success_response(data=page_data)


# ===== 9.2 新增教练 =====

@coaches_router.post("")
async def create_coach(
    coach: CoachCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles("admin")),
):
    """创建教练（管理员）。

    除了教练档案，还会开一个能登录的账号（账号 = 手机号，初始密码 123456）——
    否则「新增的教练」没有账号，拿了手机号也进不了教练工作台。
    账号信息随响应返回，管理员当面把初始密码告诉本人即可。
    """
    created, username = await create_coach_obj(db, coach)
    item = CoachItem.from_coach(created)
    item["account"] = {
        "username": username,
        "password": DEFAULT_PASSWORD,
        "role": "coach",
    }
    return success_response(
        msg=f"创建成功，登录账号 {username}（初始密码 {DEFAULT_PASSWORD}）",
        data=item,
    )


# ===== 9.3 编辑教练 =====

@coaches_router.put("/{coach_id}")
async def update_coach(
    coach_id: int,
    coach: CoachUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles("admin")),
):
    """更新教练（管理员）。"""
    updated = await update_coach_obj(db, coach_id, coach)
    if updated is None:
        raise HTTPException(status_code=404, detail="教练不存在")
    return success_response(msg="修改成功", data=CoachItem.from_coach(updated))


# ===== 9.4 删除教练 =====

@coaches_router.delete("/{coach_id}")
async def delete_coach(
    coach_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles("admin")),
):
    """删除教练（管理员）。

    教练名下的课程 / 排班 / 训练计划会一并删除，学员只解除归属、不删除。
    响应里的 msg 会把「连带删了什么」说清楚，data 里带各项数量。
    """
    # 原来删不存在的教练也回「删除成功」：crud 里恒 return True，
    # 这里的 `if coach is None` 是死代码。现在 crud 会先查存在性，查不到返回 None。
    info = await delete_coach_obj(db, coach_id)
    if info is None:
        raise HTTPException(status_code=404, detail="教练不存在")

    cascaded = []
    if info["courses"]:
        cascaded.append(f"{info['courses']} 门课程")
    if info["schedules"]:
        cascaded.append(f"{info['schedules']} 条排班")
    if info["plans"]:
        cascaded.append(f"{info['plans']} 条训练计划")
    if info["appointments"]:
        cascaded.append(f"{info['appointments']} 条预约")

    msg = f"已删除教练「{info['name']}」"
    if cascaded:
        msg += f"，并连带删除 {'、'.join(cascaded)}"
    if info["students"]:
        msg += f"；{info['students']} 名学员已转为未分配"
    return success_response(msg=msg, data=info)


# ===== 9.5 教练授课统计 =====

@coaches_router.get("/{coach_id}/statistics")
async def get_coach_statistics(
    coach_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles("admin", "reception", "coach")),
):
    """获取教练统计。"""
    stat = await get_coach_statistics_obj(db, coach_id)
    if stat is None:
        raise HTTPException(status_code=404, detail="教练不存在")
    return success_response(data=stat)
