from __future__ import annotations

from app.config import settings
from app.enums import Role
from app.repositories.courier import CourierRepository


class AuthService:
    @staticmethod
    async def resolve_role(session, tg_user_id: int) -> Role | None:
        if tg_user_id in settings.admin_ids:
            return Role.ADMIN
        courier = await CourierRepository(session).get_active_by_tg_id(tg_user_id)
        return Role.COURIER if courier else None

