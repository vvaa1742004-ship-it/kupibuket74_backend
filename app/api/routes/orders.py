from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentActor, DbSession, require_role
from app.api.schemas import AssignCourierIn, OrderOut, OrderUpdateIn, StatusUpdateIn, order_item
from app.enums import OrderPriority, OrderStatus, Role
from app.models import Order
from app.repositories.courier import CourierRepository
from app.repositories.order import OrderRepository, priority_rank
from app.services.formatters import haversine_km
from app.services.orders import OrderService

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("", response_model=list[OrderOut])
async def list_orders(
    session: DbSession,
    actor: CurrentActor,
    _allowed: dict = Depends(require_role(Role.ADMIN, Role.COURIER)),
    status_filter: list[OrderStatus] | None = Query(default=None, alias="status"),
    query: str | None = None,
    priority: OrderPriority | None = None,
    pickup_point_id: int | None = None,
    courier_id: int | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> list[OrderOut]:
    stmt = (
        select(Order)
        .options(
            selectinload(Order.pickup_point),
            selectinload(Order.assigned_courier),
            selectinload(Order.history),
        )
        .order_by(priority_rank(), Order.delivery_window_end, Order.created_at)
    )
    if actor["role"] == Role.COURIER:
        stmt = stmt.where(
            or_(Order.assigned_courier_id == actor["tg_user_id"], Order.status == OrderStatus.NEW)
        )
    if status_filter:
        stmt = stmt.where(Order.status.in_(status_filter))
    if query:
        needle = f"%{query}%"
        stmt = stmt.where(
            or_(
                Order.order_number.ilike(needle),
                Order.customer_phone.ilike(needle),
                Order.recipient_phone.ilike(needle),
                Order.customer_name.ilike(needle),
                Order.recipient_name.ilike(needle),
                Order.address_text.ilike(needle),
            )
        )
    if priority:
        stmt = stmt.where(Order.priority == priority)
    if pickup_point_id:
        stmt = stmt.where(Order.pickup_point_id == pickup_point_id)
    if courier_id:
        stmt = stmt.where(Order.assigned_courier_id == courier_id)
    if date_from:
        stmt = stmt.where(Order.delivery_window_start >= date_from)
    if date_to:
        stmt = stmt.where(Order.delivery_window_end <= date_to)

    result = await session.execute(stmt.limit(100))
    return [order_item(order) for order in result.scalars().unique().all()]


@router.get("/{order_id}", response_model=OrderOut)
async def get_order(order_id: int, session: DbSession, _actor: CurrentActor) -> OrderOut:
    repo = OrderRepository(session)
    order = await repo.get(order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    location = None
    courier_distance = None
    if order.assigned_courier_id:
        location = await CourierRepository(session).latest_location(order.assigned_courier_id)
        if location and order.lat is not None and order.lon is not None:
            courier_distance = haversine_km(location.lat, location.lon, order.lat, order.lon)
    return order_item(order, location, courier_distance)


@router.patch("/{order_id}", response_model=OrderOut)
async def patch_order(
    order_id: int,
    payload: OrderUpdateIn,
    session: DbSession,
    actor: CurrentActor,
    _admin: dict = Depends(require_role(Role.ADMIN)),
) -> OrderOut:
    repo = OrderRepository(session)
    service = OrderService(session, None)
    order = await repo.get(order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    updates = payload.model_dump(exclude_none=True)
    priority = updates.pop("priority", None)
    if priority is not None:
        await service.set_priority(order_id, actor["tg_user_id"], priority)
    for field, value in updates.items():
        setattr(order, field, value)
    await session.flush()
    refreshed = await repo.get(order_id)
    return order_item(refreshed)


@router.post("/{order_id}/assign", response_model=OrderOut)
async def assign_order(
    order_id: int,
    payload: AssignCourierIn,
    session: DbSession,
    actor: CurrentActor,
    _admin: dict = Depends(require_role(Role.ADMIN)),
) -> OrderOut:
    order = await OrderService(session, None).assign_to_courier_admin(
        order_id, payload.courier_id, actor["tg_user_id"]
    )
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order_item(order)


@router.post("/{order_id}/status", response_model=OrderOut)
async def update_order_status(
    order_id: int,
    payload: StatusUpdateIn,
    session: DbSession,
    actor: CurrentActor,
) -> OrderOut:
    service = OrderService(session, None)
    order = None
    if payload.status == OrderStatus.PICKED_UP:
        order = await service.mark_picked_up(order_id, actor["tg_user_id"])
    elif payload.status == OrderStatus.DELIVERED:
        order = await service.mark_delivered(
            order_id,
            actor["tg_user_id"],
            payload.proof_photo_file_id,
            payload.proof_comment,
        )
    elif payload.status == OrderStatus.PROBLEM:
        order = await service.set_problem(order_id, actor["tg_user_id"], payload.reason or "PROBLEM")
    elif payload.status == OrderStatus.CANCELED:
        order = await service.cancel(order_id, actor["tg_user_id"], payload.reason or "Canceled")
    else:
        repo = OrderRepository(session)
        order = await repo.get(order_id)
        if order is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
        await repo.update_status(order, payload.status, actor["tg_user_id"], payload.reason)

    if order is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Status update failed")
    refreshed = await OrderRepository(session).get(order.id)
    return order_item(refreshed)

