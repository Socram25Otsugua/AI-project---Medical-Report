from app.routers.health import router as health_router
from app.routers.history import router as history_router
from app.routers.reports import router as reports_router

__all__ = ["health_router", "reports_router", "history_router"]
