"""前台运营工作台请求与响应模型。"""
from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class ReceptionCreate(BaseModel):
    """管理员新增运营（前台）人员。

    与新增教练/会员同一套做法：档案与登录账号一起建，
    初始密码统一走 DEFAULT_PASSWORD，不用管理员自己想一个密码再转告。

    另有一条「补建档案」语义：手机号下**已有**运营账号时（历史上只注册过账号、
    没建档案的人），直接沿用那个账号，不新建、也不重置密码 —— 见 crud/reception.create_staff。
    前端在运营人员列表里对未建档的行点「补建档案」，走的就是这个接口。
    """
    name: str = Field(..., max_length=50, description="姓名")
    phone: str = Field(..., max_length=20, description="联系电话，同时作为登录账号")
    salary: Optional[float] = Field(None, description="薪资")
    hire_date: date = Field(..., description="入职时间")
    status: str = Field("在职", max_length=16, description="在职 / 休假 / 离职")
    remark: str = Field("", description="备注")
