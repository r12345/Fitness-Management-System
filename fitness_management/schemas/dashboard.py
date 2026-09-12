"""管理员数据大盘响应模型。"""
from pydantic import BaseModel, ConfigDict


class DashboardSummary(BaseModel):
    period: str
    total_members: int
    new_members: int
    expired_members: int
    total_revenue: float
    total_appointments: int

    model_config = ConfigDict(
        from_attributes=True
    )
