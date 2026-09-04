"""会员消费记录相关数据模型。"""
from datetime import datetime
from decimal import Decimal

from sqlalchemy import ForeignKey, String,DECIMAL
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base


class ConsumeRecord(Base):
    __tablename__ = "consume_record"
    id: Mapped[int] = mapped_column(primary_key=True, comment="消费编号")
    member_id: Mapped[int] = mapped_column(
        ForeignKey("member.id", ondelete="CASCADE"), nullable=True,comment="会员"
    )
    item: Mapped[str] = mapped_column(String(64),comment="消费项目")
    amount: Mapped[Decimal] = mapped_column(DECIMAL(10,2),comment="金额")
    pay_method: Mapped[str] = mapped_column(String(64),comment="支付方式")
    operator: Mapped[str] = mapped_column(String(64),comment="操作人")
    created_at: Mapped[datetime] = mapped_column(comment="消费时间")

    member: Mapped["Member"] = relationship(back_populates="consume_records")
