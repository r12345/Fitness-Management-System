"""会员消费记录相关数据模型。"""
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base


class ConsumeRecord(Base):
    """会员消费记录表，对应 MySQL 的 consumption_record。"""

    __tablename__ = "consumption_record"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment="消费编号")
    member_id: Mapped[int] = mapped_column(
        ForeignKey("member.id", ondelete="CASCADE"), nullable=False, comment="会员"
    )
    item: Mapped[str] = mapped_column(String(128), nullable=False, comment="消费项目")
    amount: Mapped[float] = mapped_column(Float, nullable=False, comment="金额")
    pay_method: Mapped[str] = mapped_column(String(32), nullable=False, comment="支付方式")
    operator: Mapped[str] = mapped_column(String(64), nullable=False, comment="操作人")
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        comment="消费时间"
    )

    member: Mapped["Member"] = relationship(back_populates="consume_records")
