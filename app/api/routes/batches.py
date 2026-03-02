from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentActor, DbSession, require_role
from app.api.schemas import BatchProgressOut, batch_item, order_item
from app.enums import BatchStatus, Role
from app.models import Batch
from app.repositories.courier import CourierRepository
from app.services.formatters import haversine_km
from app.services.orders import OrderService

router = APIRouter(prefix="/batches", tags=["batches"])


@router.get("/current", response_model=BatchProgressOut)
async def current_batch(
    session: DbSession,
    actor: CurrentActor,
    _courier: dict = Depends(require_role(Role.COURIER)),
) -> BatchProgressOut:
    result = await session.execute(
        select(Batch)
        .options(selectinload(Batch.orders))
        .where(Batch.courier_id == actor["tg_user_id"], Batch.status == BatchStatus.ACTIVE)
    )
    batch = result.scalar_one_or_none()
    route = await OrderService(session, None).route_for_courier(actor["tg_user_id"])
    latest = await CourierRepository(session).latest_location(actor["tg_user_id"])
    items = []
    for order in route:
        courier_distance = None
        if latest and order.lat is not None and order.lon is not None:
            courier_distance = haversine_km(latest.lat, latest.lon, order.lat, order.lon)
        items.append(order_item(order, latest, courier_distance))
    return batch_item(batch, items)

