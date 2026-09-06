"""会员消费记录相关数据库操作。"""
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from fitness_management.models import ConsumeRecord, Member
from fitness_management.schemas.consumption import ConsumptionRecordInfo


async def get_consumptions_list(member_id: int | None,
                                start_date: datetime | None,
                                end_date: datetime | None,
                                item_type: str| None,
                                page: int,
                                page_size: int,
                                db: AsyncSession):
    """获取会员消费记录列表。"""
    stmt = (
        select(
            ConsumeRecord.id,
            Member.name.label("member_name"),  # ✅别名和schema字段对齐
            ConsumeRecord.item,
            ConsumeRecord.amount,
            ConsumeRecord.pay_method,
            ConsumeRecord.created_at,
            ConsumeRecord.operator
        )
        .join(Member, onclause=Member.id == ConsumeRecord.member_id)  # ✅join条件放到onclause
    )

    if member_id:
        stmt = stmt.where(ConsumeRecord.member_id == member_id)
    if start_date:
        stmt = stmt.where(ConsumeRecord.created_at >= start_date)
    if end_date:
        stmt = stmt.where(ConsumeRecord.created_at <= end_date)
    if item_type:
        stmt = stmt.where(ConsumeRecord.item == item_type)

    offset = (page - 1) * page_size
    query = stmt.offset(offset).limit(page_size)

    # 统计总数
    total_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(total_query)
    total = total_result.scalar() or 0

    result = await db.execute(query)
    consumption_records = result.all()

    # ✅正确总页数计算
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    item_list = []
    for row in consumption_records:
        row_dict = row._asdict()
        info = ConsumptionRecordInfo.model_validate(row_dict)
        item_list.append(info)

    return item_list, total, total_pages, page_size


async def get_detail_consumption(consumption_id: int, db: AsyncSession):
    query = select(ConsumeRecord).where(ConsumeRecord.id == consumption_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()

