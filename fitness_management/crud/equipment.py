"""器材相关数据库操作。"""
from fastapi import HTTPException
from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from fitness_management.models import Equipment, Repair, MaintenanceRecord
from fitness_management.schemas.equipment import EquipmentCreateRequest, EquipmentRepairRequest, \
    EquipmentMaintenanceRequest


async def list_equipment(keyword, category, status, page, page_size, db:AsyncSession):
    stmt = select(Equipment).order_by(Equipment.id.desc())

    if keyword:
        stmt = stmt.where(
            or_(
                Equipment.name.like(f"%{keyword}%"),
                Equipment.location.like(f"%{keyword}%"),
            )
        )
    if category:
        stmt = stmt.where(Equipment.category == category)
    if status:
        stmt = stmt.where(Equipment.status == status)


    # 统计总数
    total_query = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(total_query)
    total = total_result.scalar() or 0


    offset = (page - 1) * page_size
    query = stmt.offset(offset).limit(page_size)

    result = await db.execute(query)
    equipment_list = result.scalars().all()

    # ✅正确总页数计算
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    return equipment_list, total, total_pages, page_size


async def get_equipment(equipment_id, db: AsyncSession):
    # 原来这个函数查完就结束了 —— 没有 return，调用方拿到的永远是 None。
    # 当前全项目没人调用它，先补上返回值，避免以后接上来就踩坑。
    stmt = select(Equipment).where(Equipment.id == equipment_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def add_equipment(equipment_info: EquipmentCreateRequest, db: AsyncSession):
    equipment = Equipment(**equipment_info.model_dump())
    db.add(equipment)
    await db.commit()
    await db.refresh(equipment)
    return equipment

async def update_equipment_info(equipment_id, equipment_info: EquipmentCreateRequest, db: AsyncSession):
    stmt = select(Equipment).where(Equipment.id == equipment_id)
    result = await db.execute(stmt)
    equipment = result.scalar_one_or_none()
    if not equipment:
        raise HTTPException(status_code=404, detail="器材不存在")
    for key, value in equipment_info.model_dump(exclude_unset=True).items():
        setattr(equipment, key, value)
    await db.commit()
    await db.refresh(equipment)
    return equipment


async def drop_equipment(equipment_id, db: AsyncSession):
    query = select(Equipment).where(Equipment.id == equipment_id)
    result = await db.execute(query)
    equipment = result.scalar_one_or_none()
    if equipment is None:
        raise HTTPException(status_code=404, detail="器材不存在")
    await db.delete(equipment)
    await db.commit()
    return True


async def add_repair(equipment_id, repair_info: EquipmentRepairRequest, db: AsyncSession):
    query = select(Equipment).where(Equipment.id == equipment_id)
    result = await db.execute(query)
    equipment = result.scalar_one_or_none()
    if equipment is None:
        raise HTTPException(status_code=404, detail="器材不存在")
    equipment_repair = Repair(equipment_id=equipment_id, **repair_info.model_dump())
    db.add(equipment_repair)
    equipment.status = '维修'
    await db.commit()
    await db.refresh(equipment_repair)
    await db.refresh(equipment)
    return equipment_repair

async def add_maintenance(equipment_id, maintenance_info: EquipmentMaintenanceRequest, db: AsyncSession):
    query = select(Equipment).where(Equipment.id == equipment_id)
    result = await db.execute(query)
    equipment = result.scalar_one_or_none()
    if equipment is None:
        raise HTTPException(status_code=404, detail="器材不存在")
    equipment_maintenance = MaintenanceRecord(equipment_id=equipment_id,**maintenance_info.model_dump())
    db.add(equipment_maintenance)
    await db.commit()
    await db.refresh(equipment_maintenance)

    return equipment_maintenance




