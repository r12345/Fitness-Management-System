"""系统配置、日志与字典模型。"""
from pydantic import BaseModel, ConfigDict


class SystemConfigResponse(BaseModel):
    """系统配置模型。"""
    gym_name: str
    address: str
    business_hours: str
    phone: str

    model_config = ConfigDict(
        from_attributes=True
    )


class SystemConfigRequest(BaseModel):
    """系统配置模型。"""
    gym_name: str | None= None
    address: str | None= None
    business_hours: str | None= None
    phone: str | None= None

    model_config = ConfigDict(
        from_attributes=True
    )


class DictRequest(BaseModel):
    """字典模型。"""
    dict_type: str
    dict_value: str
    status: str

    model_config = ConfigDict(
        from_attributes=True
    )