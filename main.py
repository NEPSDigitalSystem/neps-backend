from fastapi import FastAPI
from app.api import health
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI(title="NEPS API")

app.include_router(health.router)

# Instrument the app for Prometheus metrics
Instrumentator().instrument(app).expose(app)

@app.get("/")
def read_root():
    return {"message": "hello neps"}