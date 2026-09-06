"""器材、报修、盘点和保养接口。"""
from fastapi import Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from .router import equipment_router
from ...core.database import get_db
from ...crud.equipment import list_equipment, add_equipment, update_equipment_info, drop_equipment, add_repair, \
    add_maintenance
from ...schemas.equipment import EquipmentBase, EquipmentResponseInfo, EquipmentCreateRequest, EquipmentRepairRequest, \
    EquipmentMaintenanceRequest
from ...utils.res import success_response


@equipment_router.get("/")
async def get_equipment_list(
        keyword:str = Query(None),
        category: str = Query(None),
        status: str = Query(None),
        page: int = Query(default=1),
        page_size:int = Query(default=10),
        db: AsyncSession = Depends(get_db)
):
    equipment_list,total,total_pages,page_size = await list_equipment(keyword, category, status, page, page_size, db)
    items = [EquipmentBase.model_validate(equipment) for equipment in equipment_list]
    return success_response(data=EquipmentResponseInfo(items=items, total=total, page =page,page_size= page_size, total_pages= total_pages) )

@equipment_router.post("/")
async def create_equipment(equipment_info: EquipmentCreateRequest, db: AsyncSession = Depends(get_db)):
    equipment = await add_equipment(equipment_info, db)
    if equipment:
        return success_response(msg='添加成功')
    else:
        raise HTTPException(status_code=400, detail="添加失败")


@equipment_router.patch("/{equipment_id}")
async def update_equipment(equipment_id: int, equipment_info: EquipmentCreateRequest, db: AsyncSession = Depends(get_db)):
    equipment = await update_equipment_info(equipment_id,equipment_info, db)
    if equipment:
        return success_response(msg='修改成功')
    else:
        raise HTTPException(status_code=400, detail="修改失败")

@equipment_router.delete("/{equipment_id}")
async def delete_equipment(equipment_id: int, db: AsyncSession = Depends(get_db)):
    flag = await drop_equipment(equipment_id, db)
    if flag:
        return success_response(msg='删除成功')
    else:
        raise HTTPException(status_code=400, detail="删除失败")


@equipment_router.post("/{equipment_id}/repair")
async def create_repair(equipment_id:int,repair_info:EquipmentRepairRequest,db: AsyncSession = Depends(get_db)):
    equipment_repair = await add_repair(equipment_id,repair_info, db)
    if equipment_repair:
        return success_response(msg='报修成功')
    else:
        raise HTTPException(status_code=400, detail="报修失败")

@equipment_router.post("/{equipment_id}/maintenance")
async def create_maintenance(equipment_id:int,maintenance_info:EquipmentMaintenanceRequest,db: AsyncSession = Depends(get_db)):
    equipment_maintenance = await add_maintenance(equipment_id, maintenance_info, db)
    if equipment_maintenance:
        return success_response(msg='已维护')
    else:
        raise HTTPException(status_code=400, detail="未维护")
