"""会员、会员卡与消费记录模型。"""
from datetime import datetime
from typing import Text

from pydantic import BaseModel


class MemberRequest(BaseModel):
    name: str
    gender: str
    phone: str
    age:int
    card_type: str
    card_start:datetime
    card_expire:datetime
    balance: float
    status: str
    remark: str
