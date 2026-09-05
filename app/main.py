from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.database import engine, Base
from app.api import webhooks_router, recovery_router, simulation_router, audit_router, dashboard_router
import os

from contextlib import asynccontextmanager
from app.services.recovery_worker import recovery_worker

@asynccontextmanager
async def lifespan(app: FastAPI):
    await recovery_worker.start()
    yield
    await recovery_worker.stop()

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Revox API", lifespan=lifespan)

# Setup static files for Dashboard CSS/JS
os.makedirs("app/static/css", exist_ok=True)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include routers
from app.api.demo import router as demo_router

app.include_router(webhooks_router)
app.include_router(recovery_router)
app.include_router(simulation_router)
app.include_router(audit_router)
app.include_router(dashboard_router)
app.include_router(demo_router)

@app.get("/health")
def health_check():
    return {"status": "ok"}
