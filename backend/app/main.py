from contextlib import asynccontextmanager
from typing import AsyncGenerator

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.agencies import router as agencies_router
from app.api.v1.auth import router as auth_router
from app.api.v1.escalations import router as escalations_router
from app.api.v1.export import router as export_router
from app.api.v1.insights import router as insights_router
from app.api.v1.routing import router as routing_router
from app.api.v1.side_conversations import router as side_conv_router
from app.api.v1.tickets import router as tickets_router
from app.api.v1.users import router as users_router
from app.config import settings
from app.services.archival import run_archival_job
from app.services.intent_classifier import get_intent_classifier

scheduler = BackgroundScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Warm up intent classifier model
    get_intent_classifier()

    # Schedule daily ticket archival job at 02:00 UTC
    scheduler.add_job(
        run_archival_job,
        trigger=CronTrigger(hour=2, minute=0),
        id="ticket_archival_job",
        replace_existing=True,
    )
    scheduler.start()

    yield

    if scheduler.running:
        scheduler.shutdown(wait=False)


app = FastAPI(
    title="OpsDesk API",
    version="1.0.0",
    description="Operational Helpdesk and Ticket Management System for TBO",
    lifespan=lifespan,
)

# Configure CORS
origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()]
if not origins:
    origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Row-Count"],
)

# Include API v1 routers
app.include_router(agencies_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(tickets_router, prefix="/api/v1")
app.include_router(routing_router, prefix="/api/v1")
app.include_router(side_conv_router, prefix="/api/v1")
app.include_router(escalations_router, prefix="/api/v1")
app.include_router(insights_router, prefix="/api/v1")
app.include_router(export_router, prefix="/api/v1")


@app.get("/health", tags=["health"])
def health_check() -> dict:
    return {"status": "ok", "service": "OpsDesk API", "version": "1.0.0"}
