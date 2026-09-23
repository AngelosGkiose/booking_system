from fastapi import FastAPI
from app.routers.reservations import router as reservations_router
from app.routers.auth import router as auth
from app.routers.monitoring import router as monitoring_router
from app.routers.health_router import router as health_router
app = FastAPI()

app.include_router(reservations_router)
app.include_router(auth)
app.include_router(monitoring_router)
app.include_router(health_router)