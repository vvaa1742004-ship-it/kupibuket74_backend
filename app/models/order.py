from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.enums import OrderPriority, OrderStatus
from app.models.base import Base, TimestampMixin


class Order(Base, TimestampMixin):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_number: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_phone: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    recipient_name: Mapped[str] = mapped_column(String(255), nullable=False)
    recipient_phone: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    delivery_window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    delivery_window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    address_text: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    entrance: Mapped[str | None] = mapped_column(String(32), nullable=True)
    floor: Mapped[str | None] = mapped_column(String(32), nullable=True)
    apartment: Mapped[str | None] = mapped_column(String(32), nullable=True)
    intercom_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lon: Mapped[float | None] = mapped_column(Float, nullable=True)
    pickup_point_id: Mapped[int] = mapped_column(ForeignKey("pickup_points.id"), nullable=False)
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, name="order_status"), default=OrderStatus.NEW, nullable=False, index=True
    )
    priority: Mapped[OrderPriority] = mapped_column(
        Enum(OrderPriority, name="order_priority"), default=OrderPriority.NORMAL, nullable=False, index=True
    )
    assigned_courier_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("couriers.tg_user_id"), nullable=True, index=True
    )
    batch_id: Mapped[int | None] = mapped_column(ForeignKey("batches.id"), nullable=True, index=True)
    assigned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    picked_up_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    eta_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    distance_km: Mapped[float | None] = mapped_column(Float, nullable=True)
    problem_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    canceled_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    proof_photo_file_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    proof_comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    pickup_point = relationship("PickupPoint", back_populates="orders")
    assigned_courier = relationship("Courier", back_populates="orders")
    batch = relationship("Batch", back_populates="orders")
    history = relationship("OrderStatusHistory", back_populates="order")

