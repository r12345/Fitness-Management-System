"""系统配置、日志与字典接口。"""
from datetime import date
from typing import Optional

from fastapi import Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from .router import system_router
from ...core.database import get_db
from ...core.security import require_roles
from ...crud.system import get_config_system, update_config_system, get_system_logs, get_system_dicts, \
    create_system_dict, get_log_meta
from ...models import User
from ...schemas.system import SystemConfigResponse, SystemConfigRequest, DictRequest
from ...utils.res import success_response


@system_router.get("/config")
async def get_system_config(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    data = await get_config_system(db)
    return success_response(data=SystemConfigResponse(**data))


@system_router.put("/config")
async def update_system_config(
    system_config: SystemConfigRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    # update_config_system 返回 {"key": 是否成功} 字典。
    # 原来写的是 flag1, flag2, flag3, flag4 = <dict>，解包拿到的是 key 字符串（恒为真），
    # 于是失败分支成了死代码、永远回「更新成功」。
    result = await update_config_system(system_config, db)
    failed = [key for key, ok in result.items() if not ok]
    if failed:
        raise HTTPException(status_code=400, detail=f"更新失败：{'、'.join(failed)}")
    return success_response(msg='更新成功')


@system_router.get("/logs")
async def list_system_logs(
    log_type: Optional[str] = Query(None),
    role: Optional[str] = Query(None, description="按身份筛选：admin/reception/coach/member"),
    # 这里的 user 是「操作人」查询条件，与登录用户依赖同名，故依赖变量改叫 current_user
    user: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    """操作日志（仅超级管理员）。

    四个身份（超级管理员 / 前台运营 / 健身教练 / 普通会员）的操作都写在同一张
    ``sys_log`` 里，靠 ``role`` 区分，这里按 ``role`` 筛。
    """
    data = await get_system_logs(log_type, role, user, start_date, end_date, page, page_size, db)
    return success_response(data=data)


@system_router.get("/logs/meta")
async def get_system_log_filter_meta(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    """日志筛选下拉的数据源（仅超级管理员）。

    类型从数据里现取（含条数），而不是前端写死一份清单 ——
    写死的那份和库里实际存的值对不上时，用户一选就查空，还看不出是为什么。
    """
    return success_response(data=await get_log_meta(db))


@system_router.get("/dicts")
async def list_system_dicts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    """获取系统字典。"""
    dict_list = await get_system_dicts(db)
    return success_response(data=dict_list)

@system_router.post('/dicts')
async def create_system_dicts(
    dict_info: DictRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    dict_info = await create_system_dict(dict_info, db)
    if dict_info:
        return success_response(msg='创建成功')
    else:
        raise HTTPException(status_code=400, detail="创建失败")
