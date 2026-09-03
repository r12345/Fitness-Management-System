"""教练相关数据库操作。"""
from fastapi import HTTPException
from sqlalchemy import select, func, insert, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.coach import Coach
from typing import Optional
from ..schemas.coach import CoachCreate, CoachUpdate


async def get_coach_page_list(
    db: AsyncSession,
    keyword: Optional[str],
    status: Optional[str],
    specialty: Optional[str],
    page: int,
    page_size: int
):
    stmt = select(Coach)

    # 模糊搜索 姓名 / 手机号
    if keyword:
        stmt = stmt.where(
            (Coach.name.like(f"%{keyword}%")) |

           (Coach.phone.like(f"%{keyword}%"))
        )
    # 状态筛选
    if status:
        stmt = stmt.where(Coach.status == status)
    # 专长筛选
    if specialty:
        stmt = stmt.where(Coach.specialties.like(f"%{specialty}%"))

    # 查询总条数 (异步count)
    count_stmt = select(func.count()).select_from(stmt.subquery())  # subquery把一条已经构造好的查询语句，变成一张虚拟的临时表（子查询）。
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()

    # 分页偏移
    offset = (page - 1) * page_size
    stmt = stmt.offset(offset).limit(page_size)

    # 查询分页数据
    res = await db.execute(stmt)
    coach_records = res.scalars().all()

    item_list = []
    #  把orm模型转换为字典放进item_list
    for coach in coach_records:
        spe_arr = coach.specialties.split(",") if coach.specialties else []
        item = {
            "id": coach.id,
            "name": coach.name,
            "phone": coach.phone,
            "specialties": spe_arr,
            "status": coach.status,
            "hire_date": coach.hire_date,
            "hours": coach.hours,
            "score": coach.score
        }
        item_list.append(item)

    total_pages = (total + page_size - 1) // page_size

    page_result = {
        "items": item_list,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }
    return page_result

# 创建教练
async def create_coach_obj(db: AsyncSession, coach_data: CoachCreate):
    stmt = insert(Coach).values(**coach_data.model_dump())  # Pydantic 模型转为字典
    result = await db.execute(stmt)
    await db.commit()
    return result

# 更新教练
async def update_coach_obj(db: AsyncSession, coach_id: int, coach_data: CoachUpdate):
    stmt = select(Coach).where(Coach.id == coach_id)
    result = await db.execute(stmt)
    coach = result.scalar_one_or_none()
    if not coach:
        return None
    # 更新字段
    update_data = coach_data.model_dump(exclude_unset=True)
    stmt = update(Coach).where(Coach.id == coach_id).values(**update_data)
    await db.execute(stmt)
    await db.commit()
    new_result = await db.execute(select(Coach).where(Coach.id == coach_id))
    return new_result.scalar_one_or_none()


# 删除教练
async def delete_coach_obj(db: AsyncSession, coach_id: int):
    stmt = delete(Coach).where(Coach.id == coach_id)
    result = await db.execute(stmt)
    coach = result.scalar_one_or_none()
    if not coach:
        return None
    del_stmt = delete(Coach).where(Coach.id == coach_id)
    await db.execute(del_stmt)
    await db.commit()
    return True

# 教练授课方式
async def get_coach_statistics_obj(db: AsyncSession, coach_id: int):
    pass









