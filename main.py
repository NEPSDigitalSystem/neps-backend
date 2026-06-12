from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import health
from app.routers import redcap_mock
from app.core.config import get_settings
from prometheus_fastapi_instrumentator import Instrumentator

settings = get_settings()

app = FastAPI(title="NEPS API")

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
app.include_router(redcap_mock.router)

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

