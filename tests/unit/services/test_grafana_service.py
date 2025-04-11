"""
Unit tests for Grafana service.
"""
import pytest
from unittest.mock import MagicMock, patch

from grafana_client import GrafanaApi

from app.config import Settings
from app.models.grafana import DashboardCreate, FolderCreate, DataSourceCreate
from app.services.grafana_service import GrafanaService


@pytest.fixture
def mock_grafana_client():
    """Mock GrafanaApi client."""
    mock_client = MagicMock(spec=GrafanaApi)
    
    # Mock nested attributes and responses
    mock_client.health = MagicMock()
    mock_client.health.get.return_value = {"database": "ok", "version": "9.0.0"}
    
    mock_client.search = MagicMock()
    mock_client.search.search_dashboards.return_value = [
        {
            "id": 1,
            "uid": "abcd1234",
            "title": "Test Dashboard",
            "url": "/d/abcd1234",
            "folderId": 0,
            "folderTitle": "General",
            "isStarred": False,
            "tags": ["test"]
        }
    ]
    
    mock_client.dashboard = MagicMock()
    mock_client.dashboard.get_dashboard.return_value = {
        "meta": {
            "id": 1,
            "uid": "abcd1234",
            "folderId": 0,
            "folderTitle": "General",
            "isStarred": False
        },
        "dashboard": {
            "id": 1,
            "title": "Test Dashboard",
            "tags": ["test"]
        }
    }
    mock_client.dashboard.update_dashboard.return_value = {
        "id": 2,
        "uid": "efgh5678",
        "title": "New Dashboard",
        "url": "/d/efgh5678"
    }
    
    mock_client.folder = MagicMock()
    mock_client.folder.get_all_folders.return_value = [
        {
            "id": 1,
            "uid": "folder1234",
            "title": "Test Folder",
            "url": "/dashboards/f/folder1234"
        }
    ]
    mock_client.folder.create_folder.return_value = {
        "id": 2,
        "uid": "folder5678",
        "title": "New Folder",
        "url": "/dashboards/f/folder5678"
    }
    
    mock_client.datasource = MagicMock()
    mock_client.datasource.list_datasources.return_value = [
        {
            "id": 1,
            "uid": "ds1234",
            "name": "Test Prometheus",
            "type": "prometheus",
            "url": "http://prometheus:9090",
            "access": "proxy",
            "isDefault": True
        }
    ]
    mock_client.datasource.create_datasource.return_value = {
        "datasource": {
            "id": 2,
            "uid": "ds5678",
            "name": "New Datasource",
            "type": "influxdb",
            "url": "http://influxdb:8086",
            "access": "proxy",
            "isDefault": False
        },
        "id": 2,
        "message": "Datasource added"
    }
    
    return mock_client


@pytest.fixture
def grafana_service(mock_grafana_client):
    """Create Grafana service with mocked client."""
    with patch("app.services.grafana_service.GrafanaApi.from_url", return_value=mock_grafana_client):
        service = GrafanaService(
            settings=Settings(
                GRAFANA_URL="http://test-grafana:3000",
                GRAFANA_API_KEY="test-api-key"
            )
        )
        yield service


@pytest.mark.asyncio
async def test_check_health(grafana_service, mock_grafana_client):
    """Test health check."""
    result = await grafana_service.check_health()
    
    assert result is True
    mock_grafana_client.health.get.assert_called_once()


@pytest.mark.asyncio
async def test_get_dashboards(grafana_service, mock_grafana_client):
    """Test retrieving dashboards."""
    dashboards = await grafana_service.get_dashboards()
    
    assert len(dashboards) == 1
    assert dashboards[0].id == 1
    assert dashboards[0].uid == "abcd1234"
    assert dashboards[0].title == "Test Dashboard"
    mock_grafana_client.search.search_dashboards.assert_called_once_with()


@pytest.mark.asyncio
async def test_get_dashboards_with_folder(grafana_service, mock_grafana_client):
    """Test retrieving dashboards filtered by folder."""
    dashboards = await grafana_service.get_dashboards(folder_id=1)
    
    assert len(dashboards) == 1
    mock_grafana_client.search.search_dashboards.assert_called_once_with(folder_ids=[1])


@pytest.mark.asyncio
async def test_get_dashboard(grafana_service, mock_grafana_client):
    """Test retrieving a specific dashboard."""
    dashboard = await grafana_service.get_dashboard("abcd1234")
    
    assert dashboard is not None
    assert dashboard.uid == "abcd1234"
    assert dashboard.title == "Test Dashboard"
    mock_grafana_client.dashboard.get_dashboard.assert_called_once_with("abcd1234")


@pytest.mark.asyncio
async def test_get_dashboard_not_found(grafana_service, mock_grafana_client):
    """Test retrieving a non-existent dashboard."""
    mock_grafana_client.dashboard.get_dashboard.return_value = None
    
    dashboard = await grafana_service.get_dashboard("nonexistent")
    
    assert dashboard is None
    mock_grafana_client.dashboard.get_dashboard.assert_called_once_with("nonexistent")


@pytest.mark.asyncio
async def test_create_dashboard(grafana_service, mock_grafana_client):
    """Test creating a dashboard."""
    # Mock get_dashboard to return the newly created dashboard
    dashboard_json = {"title": "New Dashboard", "panels": []}
    new_dashboard = DashboardCreate(
        dashboard_json=dashboard_json,
        folder_id=0,
        overwrite=False,
        message="Test creation"
    )
    
    result = await grafana_service.create_dashboard(new_dashboard)
    
    assert result is not None
    mock_grafana_client.dashboard.update_dashboard.assert_called_once()
    # The service should call get_dashboard to retrieve the created dashboard
    mock_grafana_client.dashboard.get_dashboard.assert_called_once()


@pytest.mark.asyncio
async def test_delete_dashboard(grafana_service, mock_grafana_client):
    """Test deleting a dashboard."""
    result = await grafana_service.delete_dashboard("abcd1234")
    
    assert result is True
    mock_grafana_client.dashboard.get_dashboard.assert_called_once_with("abcd1234")
    mock_grafana_client.dashboard.delete_dashboard.assert_called_once_with("abcd1234")


@pytest.mark.asyncio
async def test_delete_dashboard_not_found(grafana_service, mock_grafana_client):
    """Test deleting a non-existent dashboard."""
    mock_grafana_client.dashboard.get_dashboard.return_value = None
    
    result = await grafana_service.delete_dashboard("nonexistent")
    
    assert result is False
    mock_grafana_client.dashboard.get_dashboard.assert_called_once_with("nonexistent")
    mock_grafana_client.dashboard.delete_dashboard.assert_not_called()


@pytest.mark.asyncio
async def test_get_folders(grafana_service, mock_grafana_client):
    """Test retrieving folders."""
    folders = await grafana_service.get_folders()
    
    assert len(folders) == 1
    assert folders[0].id == 1
    assert folders[0].uid == "folder1234"
    assert folders[0].title == "Test Folder"
    mock_grafana_client.folder.get_all_folders.assert_called_once()


@pytest.mark.asyncio
async def test_create_folder(grafana_service, mock_grafana_client):
    """Test creating a folder."""
    new_folder = FolderCreate(title="New Folder")
    
    result = await grafana_service.create_folder(new_folder)
    
    assert result is not None
    assert result.id == 2
    assert result.uid == "folder5678"
    assert result.title == "New Folder"
    mock_grafana_client.folder.create_folder.assert_called_once_with("New Folder")


@pytest.mark.asyncio
async def test_get_datasources(grafana_service, mock_grafana_client):
    """Test retrieving data sources."""
    datasources = await grafana_service.get_datasources()
    
    assert len(datasources) == 1
    assert datasources[0].id == 1
    assert datasources[0].uid == "ds1234"
    assert datasources[0].name == "Test Prometheus"
    assert datasources[0].type == "prometheus"
    mock_grafana_client.datasource.list_datasources.assert_called_once()


@pytest.mark.asyncio
async def test_create_datasource(grafana_service, mock_grafana_client):
    """Test creating a data source."""
    new_datasource = DataSourceCreate(
        name="New Datasource",
        type="influxdb",
        url="http://influxdb:8086",
        access="proxy",
        is_default=False
    )
    
    result = await grafana_service.create_datasource(new_datasource)
    
    assert result is not None
    assert result.name == "New Datasource"
    assert result.type == "influxdb"
    assert result.url == "http://influxdb:8086"
    mock_grafana_client.datasource.create_datasource.assert_called_once()
