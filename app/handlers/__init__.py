from app.handlers.admin import router as admin_router
from app.handlers.common import router as common_router
from app.handlers.courier import router as courier_router

__all__ = ["admin_router", "common_router", "courier_router"]

