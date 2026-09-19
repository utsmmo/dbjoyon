from fastapi import FastAPI

from app.api.routes.channex_webhook import router as channex_webhook_router
from app.api.routes.health import router as health_router
from app.api.routes.hotel_templates import router as hotel_templates_router
from app.api.routes.google_sheets import router as google_sheets_router
from app.api.routes.access_admin import router as access_admin_router
from app.api.routes.admin_settings import router as admin_settings_router
from app.api.routes.hotels import router as hotels_router
from app.api.routes.incidents import router as incidents_router
from app.api.routes.notifications import router as notifications_router
from app.api.routes.review_categories import router as review_categories_router
from app.api.routes.review_analytics import router as review_analytics_router
from app.api.routes.review_insights import router as review_insights_router
from app.api.routes.reviews import router as reviews_router
from app.api.routes.review_metrics import router as review_metrics_router
from app.api.routes.sync import router as sync_router
from app.api.routes.system import router as system_router
from app.core.config import settings
from app.db.session import dispose_engine

app = FastAPI(
    title="Hotel Review Internal API",
    version="0.1.0",
    description="Internal API for review sync, incident monitoring, and future AI analysis workflows.",
)

app.include_router(health_router)
app.include_router(hotel_templates_router)
app.include_router(channex_webhook_router, prefix="/api/v1")
app.include_router(hotels_router, prefix="/api/v1")
app.include_router(access_admin_router, prefix="/api/v1")
app.include_router(admin_settings_router, prefix="/api/v1")
app.include_router(google_sheets_router, prefix="/api/v1")
app.include_router(sync_router, prefix="/api/v1")
app.include_router(reviews_router, prefix="/api/v1")
app.include_router(review_insights_router, prefix="/api/v1")
app.include_router(review_categories_router, prefix="/api/v1")
app.include_router(review_analytics_router, prefix="/api/v1")
app.include_router(review_metrics_router, prefix="/api/v1")
app.include_router(incidents_router, prefix="/api/v1")
app.include_router(notifications_router, prefix="/api/v1")
app.include_router(system_router, prefix="/api/v1")


@app.get("/", tags=["system"])
def root() -> dict[str, str]:
    return {
        "service": "hotel-review-internal-api",
        "environment": settings.app_env,
        "docs": "/docs",
    }


@app.on_event("shutdown")
def shutdown_event() -> None:
    dispose_engine()


