from __future__ import annotations

from sqlalchemy import BigInteger, Enum, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.enums import OrderStatus
from app.models.base import Base, TimestampMixin


class OrderStatusHistory(Base, TimestampMixin):
    __tablename__ = "order_status_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False, index=True)
    old_status: Mapped[OrderStatus | None] = mapped_column(
        Enum(OrderStatus, name="order_status"), nullable=True
    )
    new_status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus, name="order_status"), nullable=False)
    actor_tg_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    order = relationship("Order", back_populates="history")

