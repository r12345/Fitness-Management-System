"""会员个人中心请求与响应模型。"""
from pydantic import BaseModel, ConfigDict


class MemberCenterRequest(BaseModel):
    """会员个人中心请求模型。"""
    name: str
    phone: str
    height: float
    weight: float

    model_config = ConfigDict(
        from_attributes=True
    )