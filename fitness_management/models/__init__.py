"""SQLAlchemy 数据模型汇总。"""
from datetime import datetime, date, time
from sqlalchemy import String, Text, Float, Integer, Boolean, ForeignKey, DateTime, Date, Time, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs

class Base(AsyncAttrs, DeclarativeBase):
    """异步SQLAlchemy基类，所有模型继承"""
    pass

# 后面各个模型要在这里import，给alembic迁移识别
from .system import User, SystemConfig, SystemLog, DictItem
from .member import Member
from .consumption import ConsumptionRecord
from .coach import Coach, Schedule
from .course import Course
from .appointment import Appointment
from .training import TrainingPlan, CheckInRecord
from .equipment import Equipment, EquipmentRepair, EquipmentMaintenance




