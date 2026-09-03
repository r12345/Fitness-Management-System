"""教练信息、排班与授课统计模型。"""
from pydantic import BaseModel, Field
from typing import List, Optional, Any
from datetime import date

# 单条教练返回
class CoachItem(BaseModel):
    id: int
    name: str
    phone: str
    specialties: List[str]
    status: Optional[str]
    hire_date: Optional[date]
    class Config:
        from_attributes = True

# 分页data结构
class CoachPageData(BaseModel):
    items: List[CoachItem]
    total: int
    page: int
    page_size: int
    total_pages: int

# 统一分页响应
class CoachPageResponse(BaseModel):
    code: int = 0
    msg: str = "success"
    data: CoachPageData


# 创建教练请求模型
class CoachCreate(BaseModel):
    name: str
    phone: str
    specialties: List[str]
    salary: float
    hire_date: date
    status: str

# 更新教练：所有字段可选
class CoachUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    specialties: Optional[str] = None
    salary: Optional[float] = None
    hire_date: Optional[str] = None
    status: Optional[int] = None