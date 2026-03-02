from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import ReasonType
from app.models import PickupPoint, ProblemReason


class LookupRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def pickup_points(self) -> list[PickupPoint]:
        result = await self.session.execute(
            select(PickupPoint).where(PickupPoint.is_active.is_(True)).order_by(PickupPoint.name)
        )
        return list(result.scalars().all())

    async def get_pickup_point(self, pickup_point_id: int) -> PickupPoint | None:
        return await self.session.get(PickupPoint, pickup_point_id)

    async def reasons(self, reason_type: ReasonType) -> list[ProblemReason]:
        result = await self.session.execute(
            select(ProblemReason)
            .where(ProblemReason.type == reason_type, ProblemReason.is_active.is_(True))
            .order_by(ProblemReason.sort_order, ProblemReason.id)
        )
        return list(result.scalars().all())

    async def get_reason(self, reason_id: int) -> ProblemReason | None:
        return await self.session.get(ProblemReason, reason_id)

