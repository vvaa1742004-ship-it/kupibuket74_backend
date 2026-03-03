from __future__ import annotations

from functools import cached_property

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    bot_token: str = Field(alias="BOT_TOKEN")
    database_url: str = Field(alias="DATABASE_URL")
    alembic_database_url: str = Field(default="", alias="ALEMBIC_DATABASE_URL")
    redis_url: str = Field(default="", alias="REDIS_URL")
    admin_ids_raw: str = Field(default="", alias="ADMIN_IDS")
    fsm_ttl_seconds: int = Field(default=86400, alias="FSM_TTL_SECONDS")
    page_size: int = Field(default=5, alias="PAGE_SIZE")
    require_proof_photo_on_delivery: bool = Field(default=True, alias="REQUIRE_PROOF_PHOTO_ON_DELIVERY")
    assigned_reminder_minutes: int = Field(default=20, alias="ASSIGNED_REMINDER_MINUTES")
    picked_up_reminder_minutes: int = Field(default=45, alias="PICKED_UP_REMINDER_MINUTES")
    reminder_poll_seconds: int = Field(default=60, alias="REMINDER_POLL_SECONDS")
    enable_priority_notifications: bool = Field(default=True, alias="ENABLE_PRIORITY_NOTIFICATIONS")
    vip_repeat_minutes: int = Field(default=5, alias="VIP_REPEAT_MINUTES")
    urgent_repeat_minutes: int = Field(default=10, alias="URGENT_REPEAT_MINUTES")
    enable_batch_routing: bool = Field(default=True, alias="ENABLE_BATCH_ROUTING")
    auto_reorder_on_new_order: bool = Field(default=True, alias="AUTO_REORDER_ON_NEW_ORDER")
    enable_live_tracking: bool = Field(default=True, alias="ENABLE_LIVE_TRACKING")
    location_stale_minutes: int = Field(default=10, alias="LOCATION_STALE_MINUTES")
    jwt_secret_key: str = Field(
        default="change-me", validation_alias=AliasChoices("JWT_SECRET_KEY", "JWT_SECRET")
    )
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_expire_minutes: int = Field(default=1440, alias="JWT_EXPIRE_MINUTES")
    webapp_base_url: str = Field(
        default="http://localhost:8080",
        validation_alias=AliasChoices("WEBAPP_BASE_URL", "MINIAPP_URL"),
    )
    admin_chat_id: int | None = Field(default=None, alias="ADMIN_CHAT_ID")
    couriers_chat_id: int | None = Field(default=None, alias="COURIERS_CHAT_ID")
    api_cors_origins_raw: str = Field(
        default="",
        validation_alias=AliasChoices("API_CORS_ORIGINS", "FRONTEND_ORIGIN"),
    )
    telegram_initdata_ttl_seconds: int = Field(
        default=86400, alias="TELEGRAM_INITDATA_TTL_SECONDS"
    )

    @cached_property
    def admin_ids(self) -> set[int]:
        return {int(item.strip()) for item in self.admin_ids_raw.split(",") if item.strip()}

    @cached_property
    def api_cors_origins(self) -> list[str]:
        origins = [item.strip() for item in self.api_cors_origins_raw.split(",") if item.strip()]
        if origins:
            return origins
        return ["http://localhost:8080", "http://127.0.0.1:8080"]

    @cached_property
    def effective_alembic_database_url(self) -> str:
        if self.alembic_database_url:
            return self.alembic_database_url
        return self.database_url.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)


settings = Settings()
