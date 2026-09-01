from datetime import date
from decimal import Decimal
from typing import Text, Optional

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship


from . import Base
class Reception(Base):
    __tablename__ = "reception"
    id: Mapped[int] = mapped_column(primary_key=True, comment="前台编号")
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("user.id", ondelete="SET NULL"),
        nullable=True,
        comment="关联系统登录用户id，可为null，可不分配账号"
    )
    name: Mapped[str] = mapped_column(String(64),comment="姓名")
    phone: Mapped[str] = mapped_column(String(64),comment="联系电话")
    salary: Mapped[Optional[Decimal]] = mapped_column(nullable=True, comment="薪资")
    hire_date: Mapped[date] = mapped_column(comment="入职时间")
    status: Mapped[str] = mapped_column(String(64),comment="状态")
    remark: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, comment="备注")

    # 关联登录用户
    user: Mapped[Optional["User"]] = relationship(back_populates="reception_info")