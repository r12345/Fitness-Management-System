"""会员消费记录请求与响应模型。"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class ConsumptionRecordInfo(BaseModel):
    id: int
    member_name: str
    item: str
    amount: float
    pay_method: str
    created_at: datetime
    operator: str

    model_config = ConfigDict(
        from_attributes=True
    )


class ConsumptionResponse(BaseModel):
    items : List[ConsumptionRecordInfo]
    total : int
    page: int
    page_size: int
    total_pages: int
    model_config = ConfigDict(
        from_attributes=True
    )
