from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.enums import BatchStatus, OrderPriority, OrderStatus, Role
from app.models import Batch, Courier, CourierLocation, Order, OrderStatusHistory
from app.services.formatters import maps_link, priority_label


class AuthRequest(BaseModel):
    init_data: str


class ActorOut(BaseModel):
    tg_user_id: int
    role: Role
    full_name: str | None = None
    phone: str | None = None


class AuthResponse(BaseModel):
    access_token: str
    actor: ActorOut


class CourierOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tg_user_id: int
    full_name: str
    phone: str
    is_active: bool


class CourierLocationOut(BaseModel):
    lat: float
    lon: float
    timestamp: datetime
    map_url: str


class StatusHistoryOut(BaseModel):
    old_status: OrderStatus | None
    new_status: OrderStatus
    actor_tg_user_id: int
    note: str | None
    created_at: datetime


class OrderOut(BaseModel):
    id: int
    order_number: str
    priority: OrderPriority
    priority_label: str
    status: OrderStatus
    customer_name: str
    customer_phone: str
    recipient_name: str
    recipient_phone: str
    delivery_window_start: datetime
    delivery_window_end: datetime
    comment: str | None
    address_text: str
    entrance: str | None
    floor: str | None
    apartment: str | None
    intercom_code: str | None
    details: str | None
    lat: float | None
    lon: float | None
    pickup_point_id: int
    pickup_point_name: str | None
    pickup_point_address: str | None
    assigned_courier_id: int | None
    assigned_courier_name: str | None
    batch_id: int | None
    created_at: datetime
    assigned_at: datetime | None
    picked_up_at: datetime | None
    delivered_at: datetime | None
    duration_minutes: int | None
    eta_minutes: int | None
    distance_km: float | None
    problem_reason: str | None
    canceled_reason: str | None
    proof_photo_file_id: str | None
    proof_comment: str | None
    courier_distance_km: float | None = None
    courier_location: CourierLocationOut | None = None
    history: list[StatusHistoryOut] = []


class BatchProgressOut(BaseModel):
    batch_id: int | None
    status: BatchStatus | None
    completed: int
    remaining: int
    total: int
    next_order_id: int | None
    orders: list[OrderOut]


class OrderUpdateIn(BaseModel):
    comment: str | None = None
    address_text: str | None = None
    entrance: str | None = None
    floor: str | None = None
    apartment: str | None = None
    intercom_code: str | None = None
    details: str | None = None
    lat: float | None = None
    lon: float | None = None
    priority: OrderPriority | None = None


class StatusUpdateIn(BaseModel):
    status: OrderStatus
    reason: str | None = None
    proof_photo_file_id: str | None = None
    proof_comment: str | None = None


class AssignCourierIn(BaseModel):
    courier_id: int


class LocationUpdateIn(BaseModel):
    lat: float
    lon: float


class AnalyticsSummaryOut(BaseModel):
    summary: str
    couriers: list[dict[str, Any]]
    pickup_points: list[dict[str, Any]]


def actor_out(role: Role, tg_user_id: int, courier: Courier | None) -> ActorOut:
    if courier is None:
        return ActorOut(tg_user_id=tg_user_id, role=role)
    return ActorOut(
        tg_user_id=tg_user_id, role=role, full_name=courier.full_name, phone=courier.phone
    )


def history_items(items: list[OrderStatusHistory]) -> list[StatusHistoryOut]:
    return [
        StatusHistoryOut(
            old_status=item.old_status,
            new_status=item.new_status,
            actor_tg_user_id=item.actor_tg_user_id,
            note=item.note,
            created_at=item.created_at,
        )
        for item in sorted(items, key=lambda row: row.created_at, reverse=True)
    ]


def location_item(location: CourierLocation | None) -> CourierLocationOut | None:
    if location is None:
        return None
    return CourierLocationOut(
        lat=location.lat,
        lon=location.lon,
        timestamp=location.timestamp,
        map_url=maps_link(location.lat, location.lon),
    )


def order_item(
    order: Order,
    location: CourierLocation | None = None,
    courier_distance_km: float | None = None,
) -> OrderOut:
    return OrderOut(
        id=order.id,
        order_number=order.order_number,
        priority=order.priority,
        priority_label=priority_label(order.priority),
        status=order.status,
        customer_name=order.customer_name,
        customer_phone=order.customer_phone,
        recipient_name=order.recipient_name,
        recipient_phone=order.recipient_phone,
        delivery_window_start=order.delivery_window_start,
        delivery_window_end=order.delivery_window_end,
        comment=order.comment,
        address_text=order.address_text,
        entrance=order.entrance,
        floor=order.floor,
        apartment=order.apartment,
        intercom_code=order.intercom_code,
        details=order.details,
        lat=order.lat,
        lon=order.lon,
        pickup_point_id=order.pickup_point_id,
        pickup_point_name=order.pickup_point.name if order.pickup_point else None,
        pickup_point_address=order.pickup_point.address_text if order.pickup_point else None,
        assigned_courier_id=order.assigned_courier_id,
        assigned_courier_name=order.assigned_courier.full_name if order.assigned_courier else None,
        batch_id=order.batch_id,
        created_at=order.created_at,
        assigned_at=order.assigned_at,
        picked_up_at=order.picked_up_at,
        delivered_at=order.delivered_at,
        duration_minutes=order.duration_minutes,
        eta_minutes=order.eta_minutes,
        distance_km=order.distance_km,
        problem_reason=order.problem_reason,
        canceled_reason=order.canceled_reason,
        proof_photo_file_id=order.proof_photo_file_id,
        proof_comment=order.proof_comment,
        courier_distance_km=courier_distance_km,
        courier_location=location_item(location),
        history=history_items(order.history),
    )


def batch_item(batch: Batch | None, orders: list[OrderOut]) -> BatchProgressOut:
    total = len(orders)
    completed = sum(
        1 for order in orders if order.status in {OrderStatus.DELIVERED, OrderStatus.CANCELED}
    )
    return BatchProgressOut(
        batch_id=batch.id if batch else None,
        status=batch.status if batch else None,
        completed=completed,
        remaining=total - completed,
        total=total,
        next_order_id=orders[0].id if orders else None,
        orders=orders,
    )

