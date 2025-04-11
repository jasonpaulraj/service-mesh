"""
Unit tests for health check endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime


def test_health_check(client, mock_uptime_kuma_service, mock_prometheus_service, mock_grafana_service, mock_proxmox_service):
    """
    Test health check endpoint returns correct response structure.
    """
    response = client.get("/api/v1/health/")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] in ["healthy", "degraded", "unhealthy"]
    assert "timestamp" in data
    assert "services" in data
    
    # Check services structure
    services = data["services"]
    assert "uptime_kuma" in services
    assert "prometheus" in services
    assert "grafana" in services
    assert "proxmox" in services
    
    # Check individual service structure
    for service_name, service_data in services.items():
        assert "status" in service_data
        assert service_data["status"] in ["healthy", "unhealthy", "unknown"]
        assert "message" in service_data


def test_ping_endpoint(client):
    """
    Test ping endpoint returns correct response.
    """
    response = client.get("/api/v1/health/ping")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "ok"
    assert data["message"] == "pong"


def test_health_check_degraded(client, monkeypatch, mock_uptime_kuma_service, mock_prometheus_service, mock_grafana_service, mock_proxmox_service):
    """
    Test health check endpoint reports degraded status when a service is unhealthy.
    """
    # Mock service to fail health check
    class MockFailingPrometheusService:
        async def check_health(self):
            raise Exception("Prometheus connection error")
    
    monkeypatch.setattr("app.api.endpoints.health.PrometheusService", MockFailingPrometheusService)
    
    response = client.get("/api/v1/health/")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "degraded"
    assert "timestamp" in data
    assert "services" in data
    
    # Check that Prometheus is reported as unhealthy
    services = data["services"]
    assert services["prometheus"]["status"] == "unhealthy"
    assert "Prometheus connection error" in services["prometheus"]["message"]


def test_health_check_integrates_all_services(client, mock_uptime_kuma_service, mock_prometheus_service, mock_grafana_service, mock_proxmox_service):
    """
    Test health check endpoint calls health check methods for all services.
    """
    # Spy on the service health check methods to verify they're called
    call_counts = {
        "uptime_kuma": 0,
        "prometheus": 0,
        "grafana": 0,
        "proxmox": 0
    }
    
    original_uptime_kuma_check = mock_uptime_kuma_service.check_health
    original_prometheus_check = mock_prometheus_service.check_health
    original_grafana_check = mock_grafana_service.check_health
    original_proxmox_check = mock_proxmox_service.check_health
    
    async def uptime_kuma_spy():
        call_counts["uptime_kuma"] += 1
        return await original_uptime_kuma_check()
    
    async def prometheus_spy():
        call_counts["prometheus"] += 1
        return await original_prometheus_check()
    
    async def grafana_spy():
        call_counts["grafana"] += 1
        return await original_grafana_check()
    
    async def proxmox_spy():
        call_counts["proxmox"] += 1
        return await original_proxmox_check()
    
    mock_uptime_kuma_service.check_health = uptime_kuma_spy
    mock_prometheus_service.check_health = prometheus_spy
    mock_grafana_service.check_health = grafana_spy
    mock_proxmox_service.check_health = proxmox_spy
    
    # Call the health check endpoint
    response = client.get("/api/v1/health/")
    assert response.status_code == 200
    
    # Check that all service health check methods were called
    assert call_counts["uptime_kuma"] == 1
    assert call_counts["prometheus"] == 1
    assert call_counts["grafana"] == 1
    assert call_counts["proxmox"] == 1
