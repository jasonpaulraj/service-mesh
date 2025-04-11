"""
Unit tests for Prometheus service.
"""
import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

from prometheus_api_client import PrometheusConnect

from app.config import Settings
from app.services.prometheus_service import PrometheusService


@pytest.fixture
def mock_prometheus_client():
    """Mock PrometheusConnect client."""
    mock_client = MagicMock(spec=PrometheusConnect)
    
    # Mock responses
    mock_client.custom_query.return_value = [
        {
            "metric": {"__name__": "up", "instance": "localhost:9090", "job": "prometheus"},
            "value": [1623860998.456, "1"]
        }
    ]
    mock_client.custom_query_range.return_value = [
        {
            "metric": {"__name__": "up", "instance": "localhost:9090", "job": "prometheus"},
            "values": [
                [1623860998.456, "1"],
                [1623861058.456, "1"]
            ]
        }
    ]
    mock_client.all_alerts.return_value = [
        {
            "labels": {"alertname": "InstanceDown", "severity": "critical"},
            "annotations": {"description": "Instance is down", "summary": "Instance down"},
            "state": "firing",
            "activeAt": "2023-01-01T00:00:00Z",
            "value": 1.0
        }
    ]
    mock_client.all_metrics.return_value = ["up", "http_requests_total", "node_cpu_seconds_total"]
    mock_client.get_metadata.return_value = {
        "up": {
            "type": "gauge",
            "help": "1 if the target is up, 0 if the target is down",
            "unit": ""
        }
    }
    
    return mock_client


@pytest.fixture
def prometheus_service(mock_prometheus_client):
    """Create Prometheus service with mocked client."""
    with patch("app.services.prometheus_service.PrometheusConnect", return_value=mock_prometheus_client):
        service = PrometheusService(
            settings=Settings(
                PROMETHEUS_URL="http://test-prometheus:9090",
                PROMETHEUS_USERNAME="test-user",
                PROMETHEUS_PASSWORD="test-password"
            )
        )
        yield service


@pytest.mark.asyncio
async def test_check_health(prometheus_service, mock_prometheus_client):
    """Test health check."""
    result = await prometheus_service.check_health()
    
    assert result is True
    mock_prometheus_client.custom_query.assert_called_once_with(query="up")


@pytest.mark.asyncio
async def test_query(prometheus_service, mock_prometheus_client):
    """Test executing a PromQL query."""
    result = await prometheus_service.query("up")
    
    assert result.status == "success"
    assert len(result.data) == 1
    assert result.data[0]["metric"]["__name__"] == "up"
    mock_prometheus_client.custom_query.assert_called_once_with(query="up", time=None)


@pytest.mark.asyncio
async def test_query_with_time(prometheus_service, mock_prometheus_client):
    """Test executing a PromQL query with specific time."""
    query_time = datetime(2023, 1, 1, 12, 0, 0)
    
    result = await prometheus_service.query("up", query_time)
    
    assert result.status == "success"
    mock_prometheus_client.custom_query.assert_called_once_with(
        query="up", 
        time=query_time.timestamp()
    )


@pytest.mark.asyncio
async def test_query_range(prometheus_service, mock_prometheus_client):
    """Test executing a PromQL range query."""
    start_time = datetime(2023, 1, 1, 12, 0, 0)
    end_time = datetime(2023, 1, 1, 13, 0, 0)
    
    result = await prometheus_service.query_range("up", start_time, end_time, "5m")
    
    assert result.status == "success"
    assert len(result.data) == 1
    mock_prometheus_client.custom_query_range.assert_called_once_with(
        query="up",
        start_time=start_time.timestamp(),
        end_time=end_time.timestamp(),
        step="5m"
    )


@pytest.mark.asyncio
async def test_get_alerts(prometheus_service, mock_prometheus_client):
    """Test retrieving alerts."""
    result = await prometheus_service.get_alerts()
    
    assert len(result.alerts) == 1
    assert result.alerts[0]["labels"]["alertname"] == "InstanceDown"
    mock_prometheus_client.all_alerts.assert_called_once()


@pytest.mark.asyncio
async def test_list_metrics(prometheus_service, mock_prometheus_client):
    """Test listing available metrics."""
    result = await prometheus_service.list_metrics()
    
    assert len(result) == 3
    assert "up" in result
    assert "http_requests_total" in result
    mock_prometheus_client.all_metrics.assert_called_once_with(None)


@pytest.mark.asyncio
async def test_list_metrics_with_match(prometheus_service, mock_prometheus_client):
    """Test listing metrics with a filter pattern."""
    result = await prometheus_service.list_metrics("node_.*")
    
    assert len(result) == 3  # Mock always returns the same list, but in reality it would filter
    mock_prometheus_client.all_metrics.assert_called_once_with("node_.*")


@pytest.mark.asyncio
async def test_get_metadata(prometheus_service, mock_prometheus_client):
    """Test retrieving metric metadata."""
    result = await prometheus_service.get_metadata()
    
    assert "up" in result
    assert result["up"].type == "gauge"
    assert result["up"].help == "1 if the target is up, 0 if the target is down"
    mock_prometheus_client.get_metadata.assert_called_once_with(None)


@pytest.mark.asyncio
async def test_get_metadata_with_metric(prometheus_service, mock_prometheus_client):
    """Test retrieving metadata for a specific metric."""
    result = await prometheus_service.get_metadata("up")
    
    assert "up" in result
    mock_prometheus_client.get_metadata.assert_called_once_with("up")
