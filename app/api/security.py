from __future__ import annotations

import hashlib
import hmac
import json
from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qsl

import jwt
from fastapi import HTTPException, status

from app.config import settings
from app.enums import Role


def validate_telegram_init_data(init_data: str) -> dict:
    parts = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = parts.pop("hash", None)
    if not received_hash:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing hash")

    data_check_string = "\n".join(f"{key}={value}" for key, value in sorted(parts.items()))
    secret_key = hmac.new(b"WebAppData", settings.bot_token.encode(), hashlib.sha256).digest()
    calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(received_hash, calculated_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid initData")

    auth_date = int(parts.get("auth_date", "0"))
    if not auth_date:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing auth_date")
    if int(datetime.now(UTC).timestamp()) - auth_date > settings.telegram_initdata_ttl_seconds:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="initData expired")

    user_raw = parts.get("user")
    if not user_raw:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing user")
    return json.loads(user_raw)


def create_access_token(tg_user_id: int, role: Role) -> str:
    payload = {
        "sub": str(tg_user_id),
        "role": role.value,
        "exp": datetime.now(UTC) + timedelta(minutes=settings.jwt_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

