"""系统配置与日志相关数据库操作。"""
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from fitness_management.models import SystemConfig, SystemLog, DictItem
from fitness_management.schemas.system import SystemConfigRequest, DictRequest


async def get_config_system(db: AsyncSession):
    # ✅ 只执行1次SQL，一次性查询4个key
    keys = ["gym_name", "address", "business_hours", "phone"]
    query = select(SystemConfig.key, SystemConfig.value).where(SystemConfig.key.in_(keys))
    res = await db.execute(query)
    # 转为字典 {key:value}
    config_dict = {row.key: row.value for row in res.all()}

    # get获取，不存在返回空字符串，避免索引报错
    return {
        "gym_name": config_dict.get("gym_name", ""),
        "address": config_dict.get("address", ""),
        "business_hours": config_dict.get("business_hours", ""),
        "phone": config_dict.get("phone", "")
    }


async def update_config_system(system_config: SystemConfigRequest, db: AsyncSession):

    # 组装待更新数据
    update_data = [
        {"key": "gym_name", "value": system_config.gym_name},
        {"key": "address", "value": system_config.address},
        {"key": "business_hours", "value": system_config.business_hours},
        {"key": "phone", "value": system_config.phone},
    ]
    row_counts = []
    for item in update_data:
        stmt = update(SystemConfig).where(SystemConfig.key == item["key"]).values(value=item["value"])
        ret = await db.execute(stmt)
        row_counts.append(ret.rowcount)

    await db.commit()
    # 返回每个key是否更新成功
    return {
        "gym_name": row_counts[0] > 0,
        "address": row_counts[1] > 0,
        "business_hours": row_counts[2] > 0,
        "phone": row_counts[3] > 0
    }


async def get_system_logs(log_type:str ,
                           user:str,
                           start_date,
                           end_date,
                           page:int,
                           page_size:int,
                           db:AsyncSession):
    stmt = select(SystemLog)
    if log_type:
        stmt = stmt.where(SystemLog.log_type == log_type)
    if user:
        stmt = stmt.where(SystemLog.user == user)
    if start_date:
        stmt = stmt.where(SystemLog.created_at >= start_date)
    if end_date:
        stmt = stmt.where(SystemLog.created_at <= end_date)
    # 分页
    total_query = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(total_query)).scalar()
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    res = await db.execute(stmt)
    content_list = res.scalars().all()
    return {
        "total": total,
        "content_list": content_list
    }


async def get_system_dicts(db: AsyncSession):
    query = select(DictItem)
    res = await db.execute(query)
    return res.scalars().all()


async def create_system_dict(dict_info:DictRequest, db: AsyncSession):
    dicts = DictItem(**dict_info.model_dump())
    db.add(dicts)
    await db.commit()
    await db.refresh(dicts)
    return dicts
