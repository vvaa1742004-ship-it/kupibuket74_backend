from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.enums import BatchStatus
from app.models.base import Base, TimestampMixin


class Batch(Base, TimestampMixin):
    __tablename__ = "batches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    courier_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("couriers.tg_user_id"), nullable=False)
    status: Mapped[BatchStatus] = mapped_column(
        Enum(BatchStatus, name="batch_status"), default=BatchStatus.ACTIVE, nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    courier = relationship("Courier", back_populates="batches")
    orders = relationship("Order", back_populates="batch")

