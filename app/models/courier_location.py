from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class CourierLocation(Base):
    __tablename__ = "courier_locations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    courier_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("couriers.tg_user_id"), nullable=False)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lon: Mapped[float] = mapped_column(Float, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    courier = relationship("Courier", back_populates="locations")

