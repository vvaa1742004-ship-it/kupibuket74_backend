from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.security import decode_access_token
from app.db import SessionFactory
from app.enums import Role
from app.repositories.courier import CourierRepository


async def get_db_session() -> AsyncSession:
    async with SessionFactory() as session:
        yield session


DbSession = Annotated[AsyncSession, Depends(get_db_session)]


async def get_current_actor(
    session: DbSession,
    authorization: Annotated[str | None, Header()] = None,
) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    payload = decode_access_token(authorization.removeprefix("Bearer ").strip())
    tg_user_id = int(payload["sub"])
    role = Role(payload["role"])
    courier = None
    if role == Role.COURIER:
        courier = await CourierRepository(session).get_active_by_tg_id(tg_user_id)
        if courier is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Courier inactive")
    return {"tg_user_id": tg_user_id, "role": role, "courier": courier}


CurrentActor = Annotated[dict, Depends(get_current_actor)]


def require_role(*roles: Role):
    async def dependency(actor: CurrentActor) -> dict:
        if actor["role"] not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return actor

    return dependency

