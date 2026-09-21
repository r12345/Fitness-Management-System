"""会员、会员卡与消费记录模型。"""
from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class MemberRequest(BaseModel):
    name: str
    gender: str
    phone: str
    age: int
    card_type: str
    # 库里 card_start / card_expire 都是 DATE 列，前端也是日期选择器。
    # 原来标成 datetime，语义对不上，纯日期字符串还要靠解析器兜底。
    card_start: date
    card_expire: date
    balance: float
    remark: str = ""
    # 卡状态不再由表单决定：后端按 card_expire 自动推导「正常/过期」。
    # 只有显式传「暂停」时，才当作人工状态保留。
    status: str = ""
    # 归属教练：前台/管理员办卡时可以指定这位会员归谁带，不选就是无归属
    coach_id: Optional[int] = None


class StudentAssign(BaseModel):
    """教练「新增学员」请求体：只收一个会员编号。

    教练不建会员档案 —— 会员来自前台开卡或本人注册，两者都带登录账号。
    教练做的是「认领」：把这个已有会员挂到自己名下。
    所以整张 member 表的字段一个都不在这里，教练既造不出没有账号的会员，
    也没法凭空给某个学员加余额、改卡状态。
    """
    member_id: int


class RenewMember(BaseModel):
    months: int
    amount: float
    remark: str
    card_type:str
    pay_method: str
    operator : str


class MemberStatus(BaseModel):
    status:str
