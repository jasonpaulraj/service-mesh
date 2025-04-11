"""
Integration tests for Uptime Kuma API integration.
These tests are meant to run against a real Uptime Kuma instance.
Skip them in CI unless a test instance is available.
"""
import os
import pytest
from unittest.mock import patch

from app.config import Settings
from app.models.uptime_kuma import MonitorCreate, MonitorUpdate
from app.services.uptime_kuma_service import UptimeKumaService


# Check if we have environment variables for the test
# If not, we'll skip these tests
skip_if_no_credentials = pytest.mark.skipif(
    not (os.environ.get("TEST_UPTIME_KUMA_URL") and 
         os.environ.get("TEST_UPTIME_KUMA_USERNAME") and 
         os.environ.get("TEST_UPTIME_KUMA_PASSWORD")),
    reason="No Uptime Kuma test credentials provided"
)


@pytest.fixture
def uptime_kuma_service():
    """Create real Uptime Kuma service for integration testing."""
    service = UptimeKumaService(
        settings=Settings(
            UPTIME_KUMA_URL=os.environ.get("TEST_UPTIME_KUMA_URL", ""),
            UPTIME_KUMA_USERNAME=os.environ.get("TEST_UPTIME_KUMA_USERNAME", ""),
            UPTIME_KUMA_PASSWORD=os.environ.get("TEST_UPTIME_KUMA_PASSWORD", "")
        )
    )
    yield service
    # Clean up by closing the connection
    asyncio.run(service.close())


@skip_if_no_credentials
@pytest.mark.asyncio
async def test_check_health(uptime_kuma_service):
    """Test health check against real Uptime Kuma instance."""
    result = await uptime_kuma_service.check_health()
    assert result is True


@skip_if_no_credentials
@pytest.mark.asyncio
async def test_monitor_lifecycle(uptime_kuma_service):
    """
    Test full lifecycle of a monitor:
    - Create
    - Read
    - Update
    - Delete
    """
    # Create a test monitor
    monitor_data = MonitorCreate(
        name="Integration Test Monitor",
        type="http",
        url="https://httpbin.org/status/200",
        interval=60,
        description="Created by integration test"
    )
    
    created_monitor = await uptime_kuma_service.create_monitor(monitor_data)
    assert created_monitor is not None
    assert created_monitor.name == "Integration Test Monitor"
    assert created_monitor.type == "http"
    
    # Get the monitor
    monitor_id = created_monitor.id
    fetched_monitor = await uptime_kuma_service.get_monitor(monitor_id)
    assert fetched_monitor is not None
    assert fetched_monitor.id == monitor_id
    assert fetched_monitor.name == "Integration Test Monitor"
    
    # Update the monitor
    update_data = MonitorUpdate(
        name="Updated Integration Test Monitor",
        interval=120
    )
    updated_monitor = await uptime_kuma_service.update_monitor(monitor_id, update_data)
    assert updated_monitor is not None
    assert updated_monitor.name == "Updated Integration Test Monitor"
    assert updated_monitor.interval == 120
    
    # Delete the monitor
    deleted = await uptime_kuma_service.delete_monitor(monitor_id)
    assert deleted is True
    
    # Verify it's gone
    non_existent = await uptime_kuma_service.get_monitor(monitor_id)
    assert non_existent is None


@skip_if_no_credentials
@pytest.mark.asyncio
async def test_get_monitors_and_status_pages(uptime_kuma_service):
    """Test retrieving all monitors and status pages."""
    # Get all monitors
    monitors = await uptime_kuma_service.get_monitors()
    assert isinstance(monitors, list)
    
    # Get all status pages
    status_pages = await uptime_kuma_service.get_status_pages()
    assert isinstance(status_pages, list)
