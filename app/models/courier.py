from __future__ import annotations

from sqlalchemy import BigInteger, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Courier(Base, TimestampMixin):
    __tablename__ = "couriers"

    tg_user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(32), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    orders = relationship("Order", back_populates="assigned_courier")
    batches = relationship("Batch", back_populates="courier")
    locations = relationship("CourierLocation", back_populates="courier")

