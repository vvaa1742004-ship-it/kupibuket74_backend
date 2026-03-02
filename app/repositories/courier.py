from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.enums import BatchStatus, OrderStatus
from app.models import Batch, Courier, CourierLocation, Order


class CourierRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_active_by_tg_id(self, tg_user_id: int) -> Courier | None:
        result = await self.session.execute(
            select(Courier).where(Courier.tg_user_id == tg_user_id, Courier.is_active.is_(True))
        )
        return result.scalar_one_or_none()

    async def get_all_active(self) -> list[Courier]:
        result = await self.session.execute(select(Courier).where(Courier.is_active.is_(True)))
        return list(result.scalars().all())

    async def upsert(self, tg_user_id: int, full_name: str, phone: str, is_active: bool = True) -> Courier:
        courier = await self.session.get(Courier, tg_user_id)
        if courier is None:
            courier = Courier(tg_user_id=tg_user_id, full_name=full_name, phone=phone, is_active=is_active)
            self.session.add(courier)
        else:
            courier.full_name = full_name
            courier.phone = phone
            courier.is_active = is_active
        await self.session.flush()
        return courier

    async def set_active(self, tg_user_id: int, is_active: bool) -> Courier | None:
        courier = await self.session.get(Courier, tg_user_id)
        if courier:
            courier.is_active = is_active
            await self.session.flush()
        return courier

    async def get_or_create_active_batch(self, courier_id: int) -> Batch:
        result = await self.session.execute(
            select(Batch).where(Batch.courier_id == courier_id, Batch.status == BatchStatus.ACTIVE)
        )
        batch = result.scalar_one_or_none()
        if batch is None:
            batch = Batch(courier_id=courier_id, status=BatchStatus.ACTIVE)
            self.session.add(batch)
            await self.session.flush()
        return batch

    async def complete_batch_if_done(self, batch_id: int) -> None:
        batch = await self.session.get(Batch, batch_id)
        if batch is None or batch.status != BatchStatus.ACTIVE:
            return
        result = await self.session.execute(
            select(func.count(Order.id)).where(
                Order.batch_id == batch_id,
                Order.status.in_([OrderStatus.ASSIGNED, OrderStatus.PICKED_UP, OrderStatus.PROBLEM]),
            )
        )
        remaining = result.scalar_one()
        if remaining == 0:
            batch.status = BatchStatus.COMPLETED
            batch.completed_at = datetime.now(timezone.utc)
            await self.session.flush()

    async def get_active_batch_orders(self, courier_id: int) -> list[Order]:
        result = await self.session.execute(
            select(Order)
            .options(
                selectinload(Order.pickup_point),
                selectinload(Order.assigned_courier),
                selectinload(Order.history),
            )
            .join(Batch, Order.batch_id == Batch.id)
            .where(Batch.courier_id == courier_id, Batch.status == BatchStatus.ACTIVE)
        )
        return list(result.scalars().all())

    async def save_location(self, courier_id: int, lat: float, lon: float) -> CourierLocation:
        location = CourierLocation(
            courier_id=courier_id, lat=lat, lon=lon, timestamp=datetime.now(timezone.utc)
        )
        self.session.add(location)
        await self.session.flush()
        return location

    async def latest_location(self, courier_id: int) -> CourierLocation | None:
        result = await self.session.execute(
            select(CourierLocation)
            .where(CourierLocation.courier_id == courier_id)
            .order_by(CourierLocation.timestamp.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def free_couriers(self) -> list[Courier]:
        result = await self.session.execute(
            select(Courier)
            .where(Courier.is_active.is_(True))
            .where(
                ~select(Order.id)
                .where(
                    and_(
                        Order.assigned_courier_id == Courier.tg_user_id,
                        Order.status.in_([OrderStatus.ASSIGNED, OrderStatus.PICKED_UP]),
                    )
                )
                .exists()
            )
        )
        return list(result.scalars().all())

    async def stale_couriers(self, stale_minutes: int) -> list[tuple[Courier, CourierLocation]]:
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=stale_minutes)
        result = await self.session.execute(
            select(Courier, CourierLocation)
            .join(CourierLocation, CourierLocation.courier_id == Courier.tg_user_id)
            .where(CourierLocation.timestamp < cutoff)
        )
        return list(result.all())
