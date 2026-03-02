from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import case, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.enums import OrderPriority, OrderStatus
from app.models import Order, OrderStatusHistory


def priority_rank():
    return case(
        (Order.priority == OrderPriority.VIP, 0),
        (Order.priority == OrderPriority.URGENT, 1),
        else_=2,
    )


class OrderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, **kwargs) -> Order:
        order = Order(**kwargs)
        self.session.add(order)
        await self.session.flush()
        return order

    async def get(self, order_id: int) -> Order | None:
        result = await self.session.execute(
            select(Order)
            .options(
                selectinload(Order.pickup_point),
                selectinload(Order.assigned_courier),
                selectinload(Order.history),
            )
            .where(Order.id == order_id)
        )
        return result.scalar_one_or_none()

    async def list_available(self, page: int, page_size: int) -> list[Order]:
        result = await self.session.execute(
            select(Order)
            .options(selectinload(Order.pickup_point))
            .where(Order.status == OrderStatus.NEW)
            .order_by(priority_rank(), Order.delivery_window_end, Order.created_at)
            .offset(page * page_size)
            .limit(page_size + 1)
        )
        return list(result.scalars().all())

    async def list_by_courier(self, courier_id: int, active_only: bool = True) -> list[Order]:
        statuses = (
            [OrderStatus.ASSIGNED, OrderStatus.PICKED_UP, OrderStatus.PROBLEM]
            if active_only
            else [OrderStatus.DELIVERED, OrderStatus.CANCELED]
        )
        result = await self.session.execute(
            select(Order)
            .options(selectinload(Order.pickup_point))
            .where(Order.assigned_courier_id == courier_id, Order.status.in_(statuses))
            .order_by(priority_rank(), Order.delivery_window_end, Order.created_at)
        )
        return list(result.scalars().all())

    async def search(self, query: str) -> list[Order]:
        needle = f"%{query}%"
        result = await self.session.execute(
            select(Order)
            .options(selectinload(Order.pickup_point), selectinload(Order.assigned_courier))
            .where(
                or_(
                    Order.order_number.ilike(needle),
                    Order.customer_phone.ilike(needle),
                    Order.recipient_phone.ilike(needle),
                    Order.customer_name.ilike(needle),
                    Order.recipient_name.ilike(needle),
                    Order.address_text.ilike(needle),
                )
            )
            .order_by(Order.created_at.desc())
            .limit(10)
        )
        return list(result.scalars().all())

    async def assign_if_new(self, order_id: int, courier_id: int, batch_id: int) -> bool:
        result = await self.session.execute(
            update(Order)
            .where(Order.id == order_id, Order.status == OrderStatus.NEW)
            .values(
                status=OrderStatus.ASSIGNED,
                assigned_courier_id=courier_id,
                batch_id=batch_id,
                assigned_at=datetime.now(timezone.utc),
            )
        )
        await self.session.flush()
        return result.rowcount == 1

    async def update_status(
        self,
        order: Order,
        new_status: OrderStatus,
        actor_tg_user_id: int,
        note: str | None = None,
    ) -> Order:
        old_status = order.status
        order.status = new_status
        now = datetime.now(timezone.utc)
        if new_status == OrderStatus.ASSIGNED and order.assigned_at is None:
            order.assigned_at = now
        if new_status == OrderStatus.PICKED_UP:
            order.picked_up_at = now
        if new_status == OrderStatus.DELIVERED:
            order.delivered_at = now
            if order.assigned_at:
                delta = order.delivered_at - order.assigned_at
                order.duration_minutes = max(int(delta.total_seconds() // 60), 0)
        history = OrderStatusHistory(
            order_id=order.id,
            old_status=old_status,
            new_status=new_status,
            actor_tg_user_id=actor_tg_user_id,
            note=note,
        )
        self.session.add(history)
        await self.session.flush()
        return order

    async def release_from_courier(self, order: Order, actor_tg_user_id: int, note: str | None = None) -> None:
        old_status = order.status
        order.status = OrderStatus.NEW
        order.assigned_courier_id = None
        order.batch_id = None
        history = OrderStatusHistory(
            order_id=order.id,
            old_status=old_status,
            new_status=OrderStatus.NEW,
            actor_tg_user_id=actor_tg_user_id,
            note=note,
        )
        self.session.add(history)
        await self.session.flush()

    async def list_reminder_candidates(self, status: OrderStatus, older_than_minutes: int) -> list[Order]:
        cutoff = datetime.now(timezone.utc)
        time_field = Order.assigned_at if status == OrderStatus.ASSIGNED else Order.picked_up_at
        result = await self.session.execute(
            select(Order)
            .options(selectinload(Order.pickup_point), selectinload(Order.assigned_courier))
            .where(
                Order.status == status,
                time_field.is_not(None),
                func.extract("epoch", cutoff - time_field) / 60 > older_than_minutes,
            )
        )
        return list(result.scalars().all())

    async def list_unassigned_priority_candidates(self, priority: OrderPriority, older_than_minutes: int) -> list[Order]:
        result = await self.session.execute(
            select(Order)
            .options(selectinload(Order.pickup_point))
            .where(
                Order.status == OrderStatus.NEW,
                Order.priority == priority,
                func.extract("epoch", datetime.now(timezone.utc) - Order.created_at) / 60 > older_than_minutes,
            )
        )
        return list(result.scalars().all())

    async def stats_per_courier(self) -> list[dict]:
        result = await self.session.execute(
            select(
                Order.assigned_courier_id.label("courier_id"),
                func.count(Order.id).label("taken"),
                func.count(case((Order.status == OrderStatus.DELIVERED, 1))).label("delivered"),
                func.avg(Order.duration_minutes).label("avg_minutes"),
                func.count(case((Order.status == OrderStatus.PROBLEM, 1))).label("problems"),
                func.count(
                    case((Order.delivered_at > Order.delivery_window_end, 1))
                ).label("late"),
            )
            .where(Order.assigned_courier_id.is_not(None))
            .group_by(Order.assigned_courier_id)
        )
        rows = []
        for row in result.mappings():
            delivered = row["delivered"] or 0
            taken = row["taken"] or 0
            rows.append(
                {
                    "courier_id": row["courier_id"],
                    "taken": taken,
                    "delivered": delivered,
                    "avg_minutes": round(float(row["avg_minutes"] or 0), 1),
                    "problem_pct": round(((row["problems"] or 0) / taken * 100), 1) if taken else 0.0,
                    "late_pct": round(((row["late"] or 0) / delivered * 100), 1) if delivered else 0.0,
                }
            )
        return rows

    async def stats_per_pickup_point(self) -> list[dict]:
        result = await self.session.execute(
            select(
                Order.pickup_point_id.label("pickup_point_id"),
                func.count(Order.id).label("orders"),
                func.avg(Order.duration_minutes).label("avg_minutes"),
            )
            .group_by(Order.pickup_point_id)
        )
        return [dict(row) for row in result.mappings()]
