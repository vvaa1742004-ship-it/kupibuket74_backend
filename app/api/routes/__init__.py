from app.api.routes.analytics import router as analytics_router
from app.api.routes.auth import router as auth_router
from app.api.routes.batches import router as batches_router
from app.api.routes.couriers import router as couriers_router
from app.api.routes.orders import router as orders_router

__all__ = [
    "analytics_router",
    "auth_router",
    "batches_router",
    "couriers_router",
    "orders_router",
]

