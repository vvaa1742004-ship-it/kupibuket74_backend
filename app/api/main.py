from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    analytics_router,
    auth_router,
    batches_router,
    couriers_router,
    orders_router,
)
from app.config import settings

logger = logging.getLogger(__name__)
allowed_origins = settings.api_cors_origins

if not settings.api_cors_origins_raw:
    logger.warning(
        "FRONTEND_ORIGIN/API_CORS_ORIGINS is not set. "
        "CORS is restricted to localhost origins only."
    )

app = FastAPI(title="Flower Courier Mini App API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict:
    return {"ok": True}


app.include_router(auth_router, prefix="/api/v1")
app.include_router(orders_router, prefix="/api/v1")
app.include_router(couriers_router, prefix="/api/v1")
app.include_router(batches_router, prefix="/api/v1")
app.include_router(analytics_router, prefix="/api/v1")
