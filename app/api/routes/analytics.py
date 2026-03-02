from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import CurrentActor, DbSession, require_role
from app.api.schemas import AnalyticsSummaryOut
from app.enums import Role
from app.repositories.order import OrderRepository
from app.services.analytics import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary", response_model=AnalyticsSummaryOut)
async def summary(
    session: DbSession,
    _actor: CurrentActor,
    _admin: dict = Depends(require_role(Role.ADMIN)),
) -> AnalyticsSummaryOut:
    repo = OrderRepository(session)
    return AnalyticsSummaryOut(
        summary=await AnalyticsService(session).summary_text(),
        couriers=await repo.stats_per_courier(),
        pickup_points=await repo.stats_per_pickup_point(),
    )

