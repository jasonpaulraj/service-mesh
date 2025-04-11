"""
Main API router that aggregates all endpoint routers.
"""
from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.api.endpoints import (
    credentials,
    grafana,
    health,
    prometheus,
    proxmox,
    uptime_kuma,
)
from app.config import get_settings

settings = get_settings()
security = HTTPBearer()

# Create root router
root_router = APIRouter()

from fastapi.templating import Jinja2Templates

# Add this after your imports
templates = Jinja2Templates(directory="app/templates/html")

# Modify the root endpoint
@root_router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def root():
    return templates.TemplateResponse("index.html", {"request": {}})

# Create the main API router
api_router = APIRouter(prefix=settings.API_V1_STR)

# Public endpoints (no authentication required or requires login token)
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(
    credentials.router,
    prefix="/credentials",
    tags=["authentication"],
    include_in_schema=True
)

# Protected endpoints (require bearer token authentication)
api_router.include_router(
    uptime_kuma.router,
    prefix="/uptime-kuma",
    tags=["uptime-kuma"],
    dependencies=[Depends(security)]
)
api_router.include_router(
    prometheus.router,
    prefix="/prometheus",
    tags=["prometheus"],
    dependencies=[Depends(security)]
)
api_router.include_router(
    grafana.router,
    prefix="/grafana",
    tags=["grafana"],
    dependencies=[Depends(security)]
)
api_router.include_router(
    proxmox.router,
    prefix="/proxmox",
    tags=["proxmox"],
    dependencies=[Depends(security)]
)

# Combine both routers
main_router = APIRouter()
main_router.include_router(root_router)
main_router.include_router(api_router)
