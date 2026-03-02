from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.api.deps import CurrentActor, DbSession, require_role
from app.api.schemas import CourierOut, LocationUpdateIn, actor_out
from app.enums import Role
from app.models import Courier
from app.repositories.courier import CourierRepository
from app.services.orders import OrderService

router = APIRouter(prefix="/couriers", tags=["couriers"])


@router.get("", response_model=list[CourierOut])
async def list_couriers(
    session: DbSession,
    _actor: CurrentActor,
    _admin: dict = Depends(require_role(Role.ADMIN)),
) -> list[CourierOut]:
    result = await session.execute(select(Courier).order_by(Courier.full_name))
    return [CourierOut.model_validate(item) for item in result.scalars().all()]


@router.get("/me")
async def courier_me(actor: CurrentActor, _courier: dict = Depends(require_role(Role.COURIER))) -> dict:
    return {"actor": actor_out(actor["role"], actor["tg_user_id"], actor["courier"])}


@router.post("/location")
async def update_location(
    payload: LocationUpdateIn,
    session: DbSession,
    actor: CurrentActor,
    _courier: dict = Depends(require_role(Role.COURIER)),
) -> dict:
    await OrderService(session, None).save_location(actor["tg_user_id"], payload.lat, payload.lon)
    return {"ok": True}


@router.get("/{courier_id}")
async def courier_detail(
    courier_id: int,
    session: DbSession,
    _actor: CurrentActor,
    _admin: dict = Depends(require_role(Role.ADMIN)),
) -> dict:
    courier = await session.get(Courier, courier_id)
    if courier is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Courier not found")
    repo = CourierRepository(session)
    latest = await repo.latest_location(courier_id)
    active_orders = await repo.get_active_batch_orders(courier_id)
    return {
        "courier": CourierOut.model_validate(courier),
        "latest_location": {
            "lat": latest.lat,
            "lon": latest.lon,
            "timestamp": latest.timestamp,
        }
        if latest
        else None,
        "active_orders": len(active_orders),
    }

