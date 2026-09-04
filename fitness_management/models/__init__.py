"""SQLAlchemy 数据模型汇总。"""

from sqlalchemy.ext.asyncio import AsyncAttrs

from sqlalchemy.orm import DeclarativeBase


class Base(AsyncAttrs, DeclarativeBase):
    """异步SQLAlchemy基类，所有模型继承"""
    pass

# 后面各个模型要在这里import，给alembic迁移识别
from .system import User, SystemConfig, SystemLog, DictItem
from .member import Member
from .consumption import ConsumeRecord
from .coach import Coach, Schedule
from .course import Course
from .appointment import Appointment
from .training import TrainPlan, CheckinRecord, ExerciseRecord
from .equipment import Equipment,Repair,MaintenanceRecord
from .reception import Reception




