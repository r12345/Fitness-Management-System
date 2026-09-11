"""系统配置、日志与字典接口。"""
from datetime import date

from fastapi import Depends, HTTPException, Query

from .router import system_router
from ...core.database import get_db
from ...crud.system import get_config_system, update_config_system, get_system_logs, get_system_dicts, \
    create_system_dict
from ...schemas.system import SystemConfigResponse, SystemConfigRequest, DictRequest
from ...utils.res import success_response


@system_router.get("/config")
async def get_system_config(db=Depends(get_db)):
    data = await get_config_system(db)
    return success_response(data=SystemConfigResponse(**data))


@system_router.put("/config")
async def update_system_config(system_config:SystemConfigRequest,db=Depends(get_db),):
    flag1,flag2,flag3,flag4 = await update_config_system(system_config,db)
    if flag1 and flag2 and flag3 and flag4:
        return success_response(msg='更新成功')
    else:
        raise HTTPException(status_code=400, detail="更新失败")


@system_router.get("/logs")
async def list_system_logs(log_type:str =Query(None),
                           user:str=Query(None),
                           start_date:date=Query(None),
                           end_date:date=Query(None),
                           page:int=Query(1),
                           page_size:int=Query(10),
                           db=Depends(get_db)):
    data = await get_system_logs(log_type, user, start_date, end_date, page, page_size, db)
    return success_response(data=data)


@system_router.get("/dicts")
async def list_system_dicts(db=Depends(get_db)):
    """获取系统字典。"""
    dict_list = await get_system_dicts(db)
    return success_response(data=dict_list)

@system_router.post('/dicts')
async def create_system_dicts(dict_info:DictRequest,db=Depends(get_db)):
    dict_info = await create_system_dict(dict_info, db)
    if dict_info:
        return success_response(msg='创建成功')
    else:
        raise HTTPException(status_code=400, detail="创建失败")


