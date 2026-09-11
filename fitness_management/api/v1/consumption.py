"""会员消费记录接口。"""
# ========= 动态路径 {consumption_id} 放到所有路由的最底部！ =========
import csv
from datetime import datetime
from io import StringIO
from urllib.parse import quote

from fastapi import Depends, HTTPException, Query
from starlette.responses import StreamingResponse

from fitness_management.api.v1.router import consumptions_router
from fitness_management.core.database import get_db
from fitness_management.crud.consumption import get_consumptions_list, get_detail_consumption
from fitness_management.schemas.consumption import ConsumptionResponse, ConsumptionRecordInfo
from fitness_management.utils.res import success_response


@consumptions_router.get("/")
async def consumptions_list(member_id: int =Query(None),
                            start_date: datetime=Query(None),
                            end_date: datetime=Query(None),
                            item_type: str=Query(None),
                            page: int=Query(default=1),
                            page_size: int=Query(default=10),
                            db=Depends(get_db)):
    consumption_records,total,total_pages,page_size = await get_consumptions_list(member_id, start_date,end_date, item_type, page, page_size, db)
    return success_response(data=ConsumptionResponse(items=consumption_records,total=total,page=page,total_pages=total_pages,page_size=page_size))


# 导出 CSV 的列映射：字段名 -> 表头中文名
_EXPORT_COLUMNS = [
    ("id", "编号"),
    ("member_name", "会员姓名"),
    ("item", "商品名称"),
    ("amount", "消费金额"),
    ("pay_method", "支付方式"),
    ("created_at", "消费时间"),
    ("operator", "操作员"),
]


# ========= 固定路径接口写在动态id路由前面 =========
@consumptions_router.get("/export")
async def download_consume_csv(db=Depends(get_db)):
    records, _, _, _ = await get_consumptions_list(None,None,None,None,1,99999,db)

    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow([title for _, title in _EXPORT_COLUMNS])
    for record in records:
        row = record.model_dump()
        writer.writerow([row.get(field, "") for field, _ in _EXPORT_COLUMNS])

    # 加 BOM，Excel 打开中文不乱码
    payload = ("\ufeff" + buffer.getvalue()).encode("utf-8")

    filename = "会员消费记录.csv"
    encoded_name = quote(filename, encoding="utf-8")

    return StreamingResponse(
        iter([payload]),
        media_type="text/csv",
        # 注意！这里全部用普通英文减号 `-`，不要复制粘贴特殊符号
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_name}"
        }
    )


# ========= 动态路径 {consumption_id} 放到所有路由的最底部！ =========
@consumptions_router.get('/{consumption_id:int}')
async def get_consumption(consumption_id: int, db=Depends(get_db)):
    consumption_detail = await get_detail_consumption(consumption_id, db)
    if consumption_detail is None:
        raise HTTPException(status_code=404, detail="消费记录不存在")
    else:
        return success_response(data=consumption_detail)
