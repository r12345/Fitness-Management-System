from datetime import date
from typing import Optional

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base


class Reception(Base):
    """前台人员档案表，对应 MySQL 的 reception。"""

    __tablename__ = "reception"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment="前台编号")
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("sys_user.id", ondelete="SET NULL"),
        nullable=True,
        comment="关联系统登录用户id，可为null，可不分配账号"
    )
    name: Mapped[str] = mapped_column(String(64), nullable=False, comment="姓名")
    phone: Mapped[str] = mapped_column(String(20), nullable=False, comment="联系电话")
    salary: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="薪资")
    hire_date: Mapped[date] = mapped_column(nullable=False, comment="入职时间")
    status: Mapped[str] = mapped_column(String(16), nullable=False, comment="状态")
    remark: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="备注")

    user: Mapped[Optional["User"]] = relationship(back_populates="reception_info")
