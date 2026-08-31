"""SQLAlchemy 数据模型汇总。

导入本包即可将所有模型注册到 Base.metadata，供 create_all 建表使用。
"""
from .appointment import Appointment
from .coach import Coach
from .consumption import ConsumptionRecord
from .course import Course, CourseSchedule
from .equipment import Equipment, EquipmentRepair
from .member import Member
from .system import SysConfig, SysOperLog, SysUser
from .training import TrainingPlan, TrainingRecord

__all__ = [
    "Member",
    "Coach",
    "Course",
    "CourseSchedule",
    "Appointment",
    "Equipment",
    "EquipmentRepair",
    "TrainingRecord",
    "TrainingPlan",
    "ConsumptionRecord",
    "SysUser",
    "SysConfig",
    "SysOperLog",
]
