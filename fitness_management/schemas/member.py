"""会员、会员卡与消费记录模型。"""
import decimal
from datetime import datetime

from pydantic import BaseModel


class MemberRequest(BaseModel):
    name: str
    gender: str
    phone: str
    age: int
    card_type: str
    card_start: datetime
    card_expire: datetime
    balance: decimal.Decimal
    status: str
    remark: str
