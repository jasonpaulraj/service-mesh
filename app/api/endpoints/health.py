"""
Health check endpoints for the application.
"""
import logging
from datetime import datetime
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException, status

from app.models.uptime_kuma import SystemHealthResponse
from app.services.uptime_kuma_service import UptimeKumaService
from app.services.prometheus_service import PrometheusService
from app.services.grafana_service import GrafanaService
from app.services.proxmox_service import ProxmoxService
from app.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=SystemHealthResponse, summary="System Health Check")
async def health_check(
    uptime_kuma_service: UptimeKumaService = Depends(),
    prometheus_service: PrometheusService = Depends(),
    grafana_service: GrafanaService = Depends(),
    proxmox_service: ProxmoxService = Depends(),
) -> SystemHealthResponse:
    logger.info("Performing system health check")
    settings = get_settings()

    services_status = {
        "uptime_kuma": {"status": "unknown", "message": None, "enabled": "false"},
        "prometheus": {"status": "unknown", "message": None, "enabled": "false"},
        "grafana": {"status": "unknown", "message": None, "enabled": "false"},
        "proxmox": {"status": "unknown", "message": None, "enabled": "false"},
    }

    # Check Uptime Kuma
    if hasattr(settings, 'UPTIME_KUMA_URL') and settings.UPTIME_KUMA_URL:
        services_status["uptime_kuma"]["enabled"] = "true"
        try:
            await uptime_kuma_service.check_health()
            services_status["uptime_kuma"].update(
                {"status": "healthy", "message": "Connected successfully"})
        except Exception as e:
            logger.warning(
                f"Uptime Kuma health check failed: {type(e).__name__}: {str(e)}")
            services_status["uptime_kuma"].update({
                "status": "unhealthy",
                "message": f"{type(e).__name__}: {str(e)}"
            })

    # Check Prometheus
    if hasattr(settings, 'PROMETHEUS_URL') and settings.PROMETHEUS_URL:
        services_status["prometheus"]["enabled"] = "true"
        try:
            await prometheus_service.check_health()
            services_status["prometheus"].update(
                {"status": "healthy", "message": "Connected successfully"})
        except Exception as e:
            logger.warning(
                f"Prometheus health check failed: {type(e).__name__}: {str(e)}")
            services_status["prometheus"].update({
                "status": "unhealthy",
                "message": f"{type(e).__name__}: {str(e)}"
            })

    # Check Grafana
    if hasattr(settings, 'GRAFANA_URL') and settings.GRAFANA_URL:
        services_status["grafana"]["enabled"] = "true"
        try:
            await grafana_service.check_health()
            services_status["grafana"].update(
                {"status": "healthy", "message": "Connected successfully"})
        except Exception as e:
            logger.warning(
                f"Grafana health check failed: {type(e).__name__}: {str(e)}")
            services_status["grafana"].update({
                "status": "unhealthy",
                "message": f"{type(e).__name__}: {str(e)}"
            })

    # Check Proxmox
    if hasattr(settings, 'PROXMOX_URL') and settings.PROXMOX_URL:
        services_status["proxmox"]["enabled"] = "true"
        try:
            await proxmox_service.check_health()
            services_status["proxmox"].update(
                {"status": "healthy", "message": "Connected successfully"})
        except Exception as e:
            logger.warning(
                f"Proxmox health check failed: {type(e).__name__}: {str(e)}")
            services_status["proxmox"].update({
                "status": "unhealthy",
                "message": f"{type(e).__name__}: {str(e)}"
            })

    overall_status = "healthy"
    for service, status_info in services_status.items():
        if status_info["enabled"] and status_info["status"] == "unhealthy":
            overall_status = "degraded"
            break

    return SystemHealthResponse(
        status=overall_status,
        timestamp=datetime.utcnow(),
        services=services_status
    )


@router.get("/ping", summary="Ping Endpoint", response_model=Dict[str, str])
async def ping() -> Dict[str, str]:
    return {"status": "ok", "message": "pong"}
