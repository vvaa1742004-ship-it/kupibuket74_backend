from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentActor, DbSession
from app.api.schemas import AuthRequest, AuthResponse, actor_out
from app.api.security import create_access_token, validate_telegram_init_data
from app.config import settings
from app.enums import Role
from app.repositories.courier import CourierRepository

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/telegram", response_model=AuthResponse)
async def telegram_auth(payload: AuthRequest, session: DbSession) -> AuthResponse:
    user = validate_telegram_init_data(payload.init_data)
    tg_user_id = int(user["id"])
    courier = await CourierRepository(session).get_active_by_tg_id(tg_user_id)
    role = Role.ADMIN if tg_user_id in settings.admin_ids else None
    if role is None and courier:
        role = Role.COURIER
    if role is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    token = create_access_token(tg_user_id, role)
    return AuthResponse(access_token=token, actor=actor_out(role, tg_user_id, courier))


@router.get("/me")
async def me(actor: CurrentActor) -> dict:
    return {"actor": actor_out(actor["role"], actor["tg_user_id"], actor["courier"])}

