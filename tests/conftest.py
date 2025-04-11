"""
Pytest configuration module.
"""
import asyncio
import os
from typing import AsyncGenerator, Dict, Generator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.router import api_router
from app.core.exceptions import register_exception_handlers
from app.main import app as main_app
from app.services.uptime_kuma_service import UptimeKumaService
from app.services.prometheus_service import PrometheusService
from app.services.grafana_service import GrafanaService
from app.services.proxmox_service import ProxmoxService


# Set test environment
os.environ["UPTIME_KUMA_URL"] = "http://test-uptime-kuma"
os.environ["UPTIME_KUMA_USERNAME"] = "test-user"
os.environ["UPTIME_KUMA_PASSWORD"] = "test-password"
os.environ["PROMETHEUS_URL"] = "http://test-prometheus"
os.environ["GRAFANA_URL"] = "http://test-grafana"
os.environ["GRAFANA_API_KEY"] = "test-grafana-key"
os.environ["PROXMOX_URL"] = "http://test-proxmox"
os.environ["PROXMOX_USERNAME"] = "test-user"
os.environ["PROXMOX_PASSWORD"] = "test-password"
os.environ["PROXMOX_VERIFY_SSL"] = "False"


@pytest.fixture
def app() -> FastAPI:
    """
    Create a FastAPI test application.
    
    Returns:
        FastAPI: Test application
    """
    app = FastAPI()
    app.include_router(api_router)
    register_exception_handlers(app)
    return app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """
    Create a test client for the application.
    
    Args:
        app: FastAPI application
        
    Returns:
        TestClient: Test client
    """
    return TestClient(app)


@pytest.fixture
def main_client() -> TestClient:
    """
    Create a test client for the main application.
    
    Returns:
        TestClient: Test client
    """
    return TestClient(main_app)


# Mock service fixtures
@pytest.fixture
def mock_uptime_kuma_service(monkeypatch):
    """
    Mock the Uptime Kuma service.
    
    Args:
        monkeypatch: Pytest monkeypatch fixture
    """
    class MockUptimeKumaService:
        async def check_health(self):
            return True
        
        async def get_monitors(self):
            return [
                {
                    "id": 1,
                    "name": "Test Monitor",
                    "type": "http",
                    "url": "http://test-url",
                    "interval": 60,
                    "active": True,
                    "status": 1,
                    "uptime": 99.9,
                }
            ]
        
        async def get_monitor(self, monitor_id):
            if monitor_id == 1:
                return {
                    "id": 1,
                    "name": "Test Monitor",
                    "type": "http",
                    "url": "http://test-url",
                    "interval": 60,
                    "active": True,
                    "status": 1,
                    "uptime": 99.9,
                }
            return None
        
        async def create_monitor(self, monitor):
            return {
                "id": 2,
                "name": monitor.name,
                "type": monitor.type,
                "url": monitor.url,
                "interval": monitor.interval,
                "active": True,
                "status": None,
                "uptime": None,
            }
        
        async def update_monitor(self, monitor_id, monitor):
            if monitor_id == 1:
                return {
                    "id": 1,
                    "name": monitor.name if monitor.name else "Test Monitor",
                    "type": monitor.type if monitor.type else "http",
                    "url": monitor.url if monitor.url else "http://test-url",
                    "interval": monitor.interval if monitor.interval else 60,
                    "active": True,
                    "status": 1,
                    "uptime": 99.9,
                }
            return None
        
        async def delete_monitor(self, monitor_id):
            return monitor_id == 1
        
        async def get_status_pages(self):
            return [
                {
                    "id": 1,
                    "title": "Test Status Page",
                    "slug": "test-status-page",
                    "published": True,
                }
            ]
        
        async def get_status_page(self, page_id):
            if page_id == 1:
                return {
                    "id": 1,
                    "title": "Test Status Page",
                    "slug": "test-status-page",
                    "published": True,
                }
            return None
    
    monkeypatch.setattr("app.api.endpoints.health.UptimeKumaService", MockUptimeKumaService)
    monkeypatch.setattr("app.api.endpoints.uptime_kuma.UptimeKumaService", MockUptimeKumaService)
    
    return MockUptimeKumaService()


@pytest.fixture
def mock_prometheus_service(monkeypatch):
    """
    Mock the Prometheus service.
    
    Args:
        monkeypatch: Pytest monkeypatch fixture
    """
    class MockPrometheusService:
        async def check_health(self):
            return True
        
        async def query(self, query, time=None):
            return {
                "status": "success",
                "data": [
                    {
                        "metric": {"__name__": "up", "instance": "localhost:9090", "job": "prometheus"},
                        "value": [1623860998.456, "1"]
                    }
                ]
            }
        
        async def query_range(self, query, start, end, step):
            return {
                "status": "success",
                "data": [
                    {
                        "metric": {"__name__": "up", "instance": "localhost:9090", "job": "prometheus"},
                        "values": [
                            [1623860998.456, "1"],
                            [1623861058.456, "1"]
                        ]
                    }
                ]
            }
        
        async def get_alerts(self):
            return {
                "alerts": [
                    {
                        "labels": {"alertname": "TestAlert", "severity": "critical"},
                        "annotations": {"description": "This is a test alert"},
                        "state": "firing",
                        "activeAt": "2023-01-01T00:00:00Z",
                        "value": 1.0
                    }
                ]
            }
        
        async def list_metrics(self, match=None):
            return ["up", "http_requests_total", "node_cpu_seconds_total"]
        
        async def get_metadata(self, metric=None):
            return {
                "up": {
                    "type": "gauge",
                    "help": "1 if the target is up, 0 if the target is down",
                    "unit": ""
                }
            }
    
    monkeypatch.setattr("app.api.endpoints.health.PrometheusService", MockPrometheusService)
    monkeypatch.setattr("app.api.endpoints.prometheus.PrometheusService", MockPrometheusService)
    
    return MockPrometheusService()


@pytest.fixture
def mock_grafana_service(monkeypatch):
    """
    Mock the Grafana service.
    
    Args:
        monkeypatch: Pytest monkeypatch fixture
    """
    class MockGrafanaService:
        async def check_health(self):
            return True
        
        async def get_dashboards(self, folder_id=None):
            return [
                {
                    "id": 1,
                    "uid": "abcd1234",
                    "title": "Test Dashboard",
                    "url": "/d/abcd1234",
                    "folder_id": 0,
                    "folder_title": "General",
                    "is_starred": False,
                    "tags": ["test"]
                }
            ]
        
        async def get_dashboard(self, dashboard_uid):
            if dashboard_uid == "abcd1234":
                return {
                    "id": 1,
                    "uid": "abcd1234",
                    "title": "Test Dashboard",
                    "url": "/d/abcd1234",
                    "folder_id": 0,
                    "folder_title": "General",
                    "is_starred": False,
                    "tags": ["test"]
                }
            return None
        
        async def create_dashboard(self, dashboard):
            return {
                "id": 2,
                "uid": "efgh5678",
                "title": "New Dashboard",
                "url": "/d/efgh5678",
                "folder_id": dashboard.folder_id,
                "folder_title": "General",
                "is_starred": False,
                "tags": []
            }
        
        async def delete_dashboard(self, dashboard_uid):
            return dashboard_uid == "abcd1234"
        
        async def get_folders(self):
            return [
                {
                    "id": 1,
                    "uid": "folder1234",
                    "title": "Test Folder",
                    "url": "/dashboards/f/folder1234"
                }
            ]
        
        async def create_folder(self, folder):
            return {
                "id": 2,
                "uid": "folder5678",
                "title": folder.title,
                "url": f"/dashboards/f/folder5678"
            }
        
        async def get_datasources(self):
            return [
                {
                    "id": 1,
                    "uid": "ds1234",
                    "name": "Test Prometheus",
                    "type": "prometheus",
                    "url": "http://prometheus:9090",
                    "access": "proxy",
                    "is_default": True
                }
            ]
        
        async def create_datasource(self, datasource):
            return {
                "id": 2,
                "uid": "ds5678",
                "name": datasource.name,
                "type": datasource.type,
                "url": datasource.url,
                "access": datasource.access,
                "is_default": datasource.is_default
            }
    
    monkeypatch.setattr("app.api.endpoints.health.GrafanaService", MockGrafanaService)
    monkeypatch.setattr("app.api.endpoints.grafana.GrafanaService", MockGrafanaService)
    
    return MockGrafanaService()


@pytest.fixture
def mock_proxmox_service(monkeypatch):
    """
    Mock the Proxmox service.
    
    Args:
        monkeypatch: Pytest monkeypatch fixture
    """
    class MockProxmoxService:
        async def check_health(self):
            return True
        
        async def get_nodes(self):
            return [
                {
                    "id": "node1",
                    "node": "node1",
                    "status": "online",
                    "cpu": 0.1,
                    "memory": 1073741824,  # 1 GB
                    "uptime": 3600,
                    "ip": "192.168.1.1"
                }
            ]
        
        async def get_node(self, node):
            if node == "node1":
                return {
                    "id": "node1",
                    "node": "node1",
                    "status": "online",
                    "cpu": 0.1,
                    "memory": 1073741824,  # 1 GB
                    "uptime": 3600,
                    "ip": "192.168.1.1"
                }
            return None
        
        async def get_cluster_overview(self):
            return {
                "nodes": 1,
                "vms": 2,
                "storage": 1,
                "total_cpu": 4,
                "total_memory": 8589934592,  # 8 GB
                "total_disk": 107374182400  # 100 GB
            }
        
        async def get_vms(self, node=None):
            vms = [
                {
                    "vmid": 100,
                    "name": "test-vm1",
                    "status": "running",
                    "node": "node1",
                    "cpu": 1,
                    "memory": 1073741824,  # 1 GB
                    "disk": 10737418240,  # 10 GB
                    "uptime": 3600
                },
                {
                    "vmid": 101,
                    "name": "test-vm2",
                    "status": "stopped",
                    "node": "node1",
                    "cpu": 2,
                    "memory": 2147483648,  # 2 GB
                    "disk": 21474836480,  # 20 GB
                    "uptime": 0
                }
            ]
            if node:
                return [vm for vm in vms if vm["node"] == node]
            return vms
        
        async def get_vm(self, node, vmid):
            if node == "node1" and vmid == 100:
                return {
                    "vmid": 100,
                    "name": "test-vm1",
                    "status": "running",
                    "node": "node1",
                    "cpu": 1,
                    "memory": 1073741824,  # 1 GB
                    "disk": 10737418240,  # 10 GB
                    "uptime": 3600
                }
            elif node == "node1" and vmid == 101:
                return {
                    "vmid": 101,
                    "name": "test-vm2",
                    "status": "stopped",
                    "node": "node1",
                    "cpu": 2,
                    "memory": 2147483648,  # 2 GB
                    "disk": 21474836480,  # 20 GB
                    "uptime": 0
                }
            return None
        
        async def create_vm(self, node, vm):
            return {
                "vmid": 102,
                "name": vm.name,
                "status": "stopped",
                "node": node,
                "cpu": vm.cores,
                "memory": vm.memory * 1024 * 1024,  # Convert to bytes
                "disk": None,
                "uptime": 0
            }
        
        async def start_vm(self, node, vmid):
            if node == "node1" and vmid in [100, 101]:
                return f"VM {vmid} start initiated"
            raise ValueError(f"VM {vmid} not found on node {node}")
        
        async def stop_vm(self, node, vmid):
            if node == "node1" and vmid in [100, 101]:
                return f"VM {vmid} stop initiated"
            raise ValueError(f"VM {vmid} not found on node {node}")
        
        async def delete_vm(self, node, vmid):
            return node == "node1" and vmid in [100, 101]
    
    monkeypatch.setattr("app.api.endpoints.health.ProxmoxService", MockProxmoxService)
    monkeypatch.setattr("app.api.endpoints.proxmox.ProxmoxService", MockProxmoxService)
    
    return MockProxmoxService()


@pytest.fixture
def event_loop():
    """
    Create an asyncio event loop for tests.
    
    Returns:
        asyncio.AbstractEventLoop: Event loop
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
