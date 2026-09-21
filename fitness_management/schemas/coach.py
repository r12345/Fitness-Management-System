"""教练信息、排班与授课统计模型。"""
from datetime import date
from typing import List, Optional

from pydantic import BaseModel

from .common import to_payload


# 单条教练返回
class CoachItem(BaseModel):
    id: int
    name: str
    phone: str
    specialties: List[str]
    status: Optional[str]
    hire_date: Optional[date]
    hours: Optional[int]
    score:Optional[float]

    class Config:
        from_attributes = True

    @classmethod
    def from_coach(cls, coach) -> dict:
        """Coach ORM → 响应体字典。

        库里 ``specialties`` 是逗号串，而本模型的 ``specialties`` 声明成 ``List[str]``，
        直接把 ORM 丢给 ``model_validate`` 会因为类型不匹配而报错，所以先拆成数组。

        原先是 api/v1/coaches.py 里的私有函数 ``_coach_item``：
        它只负责把 ORM 转成响应体、不碰数据库，属于 schema 的职责。
        """
        return to_payload(cls(
            id=coach.id,
            name=coach.name,
            phone=coach.phone,
            specialties=coach.specialties.split(",") if coach.specialties else [],
            status=coach.status,
            hire_date=coach.hire_date,
            hours=coach.hours,
            score=coach.score,
        ))

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
    specialties: str
    salary: float
    hire_date: date
    hours: int
    score: float
    status: str

# 更新教练：所有字段可选
class CoachUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    specialties: Optional[str] = None
    salary: Optional[float] = None
    hire_date: Optional[str] = None
    status: Optional[str] = None


# 教练授课统计返回模型
class CoachStatisticsResp(BaseModel):
    coach_id: int
    total_hours: int
    student_count: int
    average_score: float
    revenue: float

    class Config:
        from_attributes = True