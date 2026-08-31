"""消费记录数据模型。"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from ..core.database import Base


class ConsumptionRecord(Base):
    """会员消费/充值记录表（前台开卡、续费、私教消费等）。"""

    __tablename__ = "consumption_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    member_id: Mapped[int] = mapped_column(
        ForeignKey("members.id", ondelete="CASCADE"), comment="消费会员"
    )
    type: Mapped[str] = mapped_column(String(20), comment="类型：开卡/续费/私教/商品/充值")
    amount: Mapped[float] = mapped_column(Numeric(10, 2), comment="金额（元）")
    balance_after: Mapped[float | None] = mapped_column(Numeric(10, 2), default=None, comment="交易后余额")
    operator: Mapped[str | None] = mapped_column(String(50), default=None, comment="操作人，如 前台小周")
    remark: Mapped[str | None] = mapped_column(String(255), default=None, comment="备注，如 续费季卡")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment="交易时间")
