from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import health
<<<<<<< HEAD
from app.api.v1 import analyst_dash
=======
from app.routers import redcap, portal
>>>>>>> 4e9a75b837d4d349c21637beb6e39f2d693359a5
from app.api.v1.redcap_sync import router as sync_router, scheduled_sync
from app.routers import portal, redcap
from app.core.config import get_settings
from prometheus_fastapi_instrumentator import Instrumentator
from apscheduler.schedulers.asyncio import AsyncIOScheduler

settings = get_settings()

scheduler = AsyncIOScheduler()
scheduler.add_job(scheduled_sync, "interval", minutes=60)

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.start()
    yield
    scheduler.shutdown()

app = FastAPI(title="NEPS API", lifespan=lifespan)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(portal.router)
app.include_router(redcap.router)
app.include_router(portal.router)
app.include_router(sync_router)
app.include_router(analyst_dash.router)

# Instrument the app for Prometheus metrics
Instrumentator().instrument(app).expose(app)


@app.get("/")
def read_root():
    return {
        "message": "hello neps",
        "app_name": settings.APP_NAME,
        "app_env": settings.APP_ENV,
        "redcap_mock_enabled": settings.REDCAP_MOCK_ENABLED
    }
