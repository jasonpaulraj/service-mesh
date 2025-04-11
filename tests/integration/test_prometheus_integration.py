"""
Integration tests for Prometheus API integration.
These tests are meant to run against a real Prometheus instance.
Skip them in CI unless a test instance is available.
"""
import os
import pytest
from datetime import datetime, timedelta

from app.config import Settings
from app.services.prometheus_service import PrometheusService


# Check if we have environment variables for the test
# If not, we'll skip these tests
skip_if_no_prometheus = pytest.mark.skipif(
    not os.environ.get("TEST_PROMETHEUS_URL"),
    reason="No Prometheus test URL provided"
)


@pytest.fixture
def prometheus_service():
    """Create real Prometheus service for integration testing."""
    service = PrometheusService(
        settings=Settings(
            PROMETHEUS_URL=os.environ.get("TEST_PROMETHEUS_URL", ""),
            PROMETHEUS_USERNAME=os.environ.get("TEST_PROMETHEUS_USERNAME", ""),
            PROMETHEUS_PASSWORD=os.environ.get("TEST_PROMETHEUS_PASSWORD", "")
        )
    )
    yield service


@skip_if_no_prometheus
@pytest.mark.asyncio
async def test_check_health(prometheus_service):
    """Test health check against real Prometheus instance."""
    result = await prometheus_service.check_health()
    assert result is True


@skip_if_no_prometheus
@pytest.mark.asyncio
async def test_query(prometheus_service):
    """Test executing PromQL query against real Prometheus instance."""
    # Query the 'up' metric which should be available in all Prometheus instances
    result = await prometheus_service.query("up")
    
    assert result.status == "success"
    assert isinstance(result.data, list)
    assert len(result.data) > 0


@skip_if_no_prometheus
@pytest.mark.asyncio
async def test_query_range(prometheus_service):
    """Test executing PromQL range query against real Prometheus instance."""
    # Query the 'up' metric over a 5-minute range
    end_time = datetime.now()
    start_time = end_time - timedelta(minutes=5)
    
    result = await prometheus_service.query_range("up", start_time, end_time, "15s")
    
    assert result.status == "success"
    assert isinstance(result.data, list)
    # The response might be empty if Prometheus has no data for that period
    # but it should be a valid response structure


@skip_if_no_prometheus
@pytest.mark.asyncio
async def test_get_alerts(prometheus_service):
    """Test retrieving alerts from real Prometheus instance."""
    result = await prometheus_service.get_alerts()
    
    assert isinstance(result.alerts, list)
    # The alerts list might be empty if no alerts are firing
    # but it should be a valid response structure


@skip_if_no_prometheus
@pytest.mark.asyncio
async def test_list_metrics(prometheus_service):
    """Test listing metrics from real Prometheus instance."""
    result = await prometheus_service.list_metrics()
    
    assert isinstance(result, list)
    assert len(result) > 0
    # 'up' metric should always be available
    assert "up" in result


@skip_if_no_prometheus
@pytest.mark.asyncio
async def test_get_metadata(prometheus_service):
    """Test retrieving metric metadata from real Prometheus instance."""
    # Get metadata for the 'up' metric
    result = await prometheus_service.get_metadata("up")
    
    assert "up" in result
    assert result["up"].type in ["gauge", "counter", "histogram", "summary"]
    assert isinstance(result["up"].help, str)
