"""
Unit tests for Uptime Kuma service.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uptime_kuma_api import UptimeKumaApi

from app.config import Settings
from app.models.uptime_kuma import MonitorCreate, MonitorUpdate
from app.services.uptime_kuma_service import UptimeKumaService


@pytest.fixture
def mock_uptime_kuma_client():
    """Mock UptimeKumaApi client."""
    mock_client = AsyncMock(spec=UptimeKumaApi)
    
    # Mock responses
    mock_client.get_info.return_value = {"version": "1.0.0"}
    mock_client.get_monitors.return_value = [
        {
            "id": 1,
            "name": "Test Monitor",
            "type": "http",
            "url": "http://test.com",
            "interval": 60,
            "active": True,
            "status": 1,
            "uptime": 99.9
        }
    ]
    mock_client.get_monitor.return_value = {
        "id": 1,
        "name": "Test Monitor",
        "type": "http",
        "url": "http://test.com",
        "interval": 60,
        "active": True,
        "status": 1,
        "uptime": 99.9
    }
    mock_client.add_monitor.return_value = {
        "id": 2,
        "name": "New Monitor",
        "type": "http",
        "url": "http://new-test.com",
        "interval": 60,
        "active": True,
        "status": None,
        "uptime": None
    }
    mock_client.edit_monitor.return_value = {
        "id": 1,
        "name": "Updated Monitor",
        "type": "http",
        "url": "http://test.com",
        "interval": 30,
        "active": True,
        "status": 1,
        "uptime": 99.9
    }
    mock_client.get_status_pages.return_value = [
        {
            "id": 1,
            "title": "Test Status Page",
            "slug": "test-status-page",
            "published": True
        }
    ]
    mock_client.get_status_page.return_value = {
        "id": 1,
        "title": "Test Status Page",
        "slug": "test-status-page",
        "published": True
    }
    
    return mock_client


@pytest.fixture
def uptime_kuma_service(mock_uptime_kuma_client):
    """Create Uptime Kuma service with mocked client."""
    with patch("app.services.uptime_kuma_service.UptimeKumaApi", return_value=mock_uptime_kuma_client):
        service = UptimeKumaService(
            settings=Settings(
                UPTIME_KUMA_URL="http://test-url",
                UPTIME_KUMA_USERNAME="test-user",
                UPTIME_KUMA_PASSWORD="test-password"
            )
        )
        yield service


@pytest.mark.asyncio
async def test_check_health(uptime_kuma_service, mock_uptime_kuma_client):
    """Test health check."""
    result = await uptime_kuma_service.check_health()
    
    assert result is True
    mock_uptime_kuma_client.get_info.assert_called_once()


@pytest.mark.asyncio
async def test_get_monitors(uptime_kuma_service, mock_uptime_kuma_client):
    """Test retrieving monitors."""
    monitors = await uptime_kuma_service.get_monitors()
    
    assert len(monitors) == 1
    assert monitors[0].id == 1
    assert monitors[0].name == "Test Monitor"
    assert monitors[0].type == "http"
    assert monitors[0].url == "http://test.com"
    mock_uptime_kuma_client.get_monitors.assert_called_once()


@pytest.mark.asyncio
async def test_get_monitor(uptime_kuma_service, mock_uptime_kuma_client):
    """Test retrieving a specific monitor."""
    monitor = await uptime_kuma_service.get_monitor(1)
    
    assert monitor is not None
    assert monitor.id == 1
    assert monitor.name == "Test Monitor"
    mock_uptime_kuma_client.get_monitor.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_get_monitor_not_found(uptime_kuma_service, mock_uptime_kuma_client):
    """Test retrieving a non-existent monitor."""
    mock_uptime_kuma_client.get_monitor.return_value = None
    
    monitor = await uptime_kuma_service.get_monitor(999)
    
    assert monitor is None
    mock_uptime_kuma_client.get_monitor.assert_called_once_with(999)


@pytest.mark.asyncio
async def test_create_monitor(uptime_kuma_service, mock_uptime_kuma_client):
    """Test creating a monitor."""
    new_monitor = MonitorCreate(
        name="New Monitor",
        type="http",
        url="http://new-test.com",
        interval=60
    )
    
    result = await uptime_kuma_service.create_monitor(new_monitor)
    
    assert result.id == 2
    assert result.name == "New Monitor"
    assert result.url == "http://new-test.com"
    mock_uptime_kuma_client.add_monitor.assert_called_once()


@pytest.mark.asyncio
async def test_update_monitor(uptime_kuma_service, mock_uptime_kuma_client):
    """Test updating a monitor."""
    update_data = MonitorUpdate(
        name="Updated Monitor",
        interval=30
    )
    
    result = await uptime_kuma_service.update_monitor(1, update_data)
    
    assert result is not None
    assert result.id == 1
    assert result.name == "Updated Monitor"
    assert result.interval == 30
    mock_uptime_kuma_client.get_monitor.assert_called_once_with(1)
    mock_uptime_kuma_client.edit_monitor.assert_called_once()


@pytest.mark.asyncio
async def test_update_monitor_not_found(uptime_kuma_service, mock_uptime_kuma_client):
    """Test updating a non-existent monitor."""
    mock_uptime_kuma_client.get_monitor.return_value = None
    
    update_data = MonitorUpdate(name="Updated Monitor")
    result = await uptime_kuma_service.update_monitor(999, update_data)
    
    assert result is None
    mock_uptime_kuma_client.get_monitor.assert_called_once_with(999)
    mock_uptime_kuma_client.edit_monitor.assert_not_called()


@pytest.mark.asyncio
async def test_delete_monitor(uptime_kuma_service, mock_uptime_kuma_client):
    """Test deleting a monitor."""
    result = await uptime_kuma_service.delete_monitor(1)
    
    assert result is True
    mock_uptime_kuma_client.get_monitor.assert_called_once_with(1)
    mock_uptime_kuma_client.delete_monitor.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_delete_monitor_not_found(uptime_kuma_service, mock_uptime_kuma_client):
    """Test deleting a non-existent monitor."""
    mock_uptime_kuma_client.get_monitor.return_value = None
    
    result = await uptime_kuma_service.delete_monitor(999)
    
    assert result is False
    mock_uptime_kuma_client.get_monitor.assert_called_once_with(999)
    mock_uptime_kuma_client.delete_monitor.assert_not_called()


@pytest.mark.asyncio
async def test_get_status_pages(uptime_kuma_service, mock_uptime_kuma_client):
    """Test retrieving status pages."""
    status_pages = await uptime_kuma_service.get_status_pages()
    
    assert len(status_pages) == 1
    assert status_pages[0].id == 1
    assert status_pages[0].title == "Test Status Page"
    assert status_pages[0].slug == "test-status-page"
    mock_uptime_kuma_client.get_status_pages.assert_called_once()


@pytest.mark.asyncio
async def test_get_status_page(uptime_kuma_service, mock_uptime_kuma_client):
    """Test retrieving a specific status page."""
    status_page = await uptime_kuma_service.get_status_page(1)
    
    assert status_page is not None
    assert status_page.id == 1
    assert status_page.title == "Test Status Page"
    mock_uptime_kuma_client.get_status_page.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_get_status_page_not_found(uptime_kuma_service, mock_uptime_kuma_client):
    """Test retrieving a non-existent status page."""
    mock_uptime_kuma_client.get_status_page.return_value = None
    
    status_page = await uptime_kuma_service.get_status_page(999)
    
    assert status_page is None
    mock_uptime_kuma_client.get_status_page.assert_called_once_with(999)


@pytest.mark.asyncio
async def test_close(uptime_kuma_service, mock_uptime_kuma_client):
    """Test closing the client connection."""
    # First we need to access the client to initialize it
    await uptime_kuma_service._get_client()
    
    # Then close the connection
    await uptime_kuma_service.close()
    
    mock_uptime_kuma_client.disconnect.assert_called_once()
