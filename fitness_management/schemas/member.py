"""会员、会员卡与消费记录模型。"""
import decimal
from datetime import datetime

from pydantic import BaseModel, Field


class MemberRequest(BaseModel):
    name: str
    gender: str
    phone: str
    age: int
    card_type: str
    card_start: datetime
    card_expire: datetime
    balance: float
    status: str
    remark: str


class RenewMember(BaseModel):
    months: int
    amount: float
    remark: str
    card_type:str
    pay_method: str
    operator : str


class MemberStatus(BaseModel):
    status:str