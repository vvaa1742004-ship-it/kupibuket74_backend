from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware

from app.config import settings
from app.enums import Role
from app.repositories.courier import CourierRepository


class AuthContextMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Any, dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        session = data.get("session")
        role = None
        courier = None
        if user:
            if user.id in settings.admin_ids:
                role = Role.ADMIN
            elif session:
                courier = await CourierRepository(session).get_active_by_tg_id(user.id)
                if courier:
                    role = Role.COURIER
        data["role"] = role
        data["courier"] = courier
        return await handler(event, data)

