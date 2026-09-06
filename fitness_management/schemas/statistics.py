"""数据统计报表模型。"""
from typing import List, Dict

from pydantic import BaseModel


class StatisticsResponse(BaseModel):
    """数据统计报表模型。"""
    coach_id : int
    coach_name : str
    hours : int
    student_count: int
    revenue : float
    average_score : float


class MemberCardDistributionResponse(BaseModel):
    """会员卡数据统计报表模型。"""
    card_type: str
    count: int

class MemberStatisticsResponse(BaseModel):
    """会员数据统计报表模型。"""
    activate_members: int
    card_distribution: List[MemberCardDistributionResponse]

