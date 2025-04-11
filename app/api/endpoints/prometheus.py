"""
Endpoints for integrating with Prometheus API.
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.models.prometheus import (
    AlertsResponse,
    MetricRange,
    MetricResponse,
    QueryResult,
)
from app.services.prometheus_service import PrometheusService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/query", response_model=QueryResult, summary="Execute PromQL Query")
async def query_prometheus(
    query: str = Query(..., description="PromQL query string"),
    time: Optional[datetime] = Query(
        None, description="Evaluation timestamp (RFC3339 or Unix timestamp)"),
    prometheus_service: PrometheusService = Depends(),
) -> QueryResult:
    """
    Execute a PromQL query against Prometheus.

    Args:
        query: PromQL query string
        time: Optional evaluation timestamp

    Returns:
        QueryResult: Query result data
    """
    try:
        result = await prometheus_service.query(query, time)
        return result
    except Exception as e:
        logger.error(f"Failed to execute Prometheus query: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute Prometheus query: {str(e)}",
        )


@router.get("/query_range", response_model=MetricRange, summary="Execute PromQL Range Query")
async def query_range(
    query: str = Query(..., description="PromQL query string"),
    start: datetime = Query(...,
                            description="Start timestamp (RFC3339 or Unix timestamp)"),
    end: datetime = Query(...,
                          description="End timestamp (RFC3339 or Unix timestamp)"),
    step: str = Query(...,
                      description="Query resolution step width (e.g. 30s, 1m, 1h)"),
    prometheus_service: PrometheusService = Depends(),
) -> MetricRange:
    """
    Execute a PromQL range query against Prometheus.

    Args:
        query: PromQL query string
        start: Start timestamp
        end: End timestamp
        step: Query resolution step width

    Returns:
        MetricRange: Range query result data
    """
    try:
        result = await prometheus_service.query_range(query, start, end, step)
        return result
    except Exception as e:
        logger.error(f"Failed to execute Prometheus range query: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute Prometheus range query: {str(e)}",
        )


@router.get("/alerts", response_model=AlertsResponse, summary="Get Active Alerts")
async def get_alerts(
    prometheus_service: PrometheusService = Depends(),
) -> AlertsResponse:
    """
    Get all active alerts from Prometheus.

    Returns:
        AlertsResponse: Active alerts data
    """
    try:
        alerts = await prometheus_service.get_alerts()
        return alerts
    except Exception as e:
        logger.error(f"Failed to get Prometheus alerts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get Prometheus alerts: {str(e)}",
        )


@router.get("/metrics", response_model=List[str], summary="List Available Metrics")
async def list_metrics(
    match: Optional[str] = Query(
        None, description="Regex pattern to match metric names"),
    prometheus_service: PrometheusService = Depends(),
) -> List[str]:
    """
    List available metrics in Prometheus.

    Args:
        match: Optional regex pattern to filter metrics

    Returns:
        List[str]: List of available metric names
    """
    try:
        metrics = await prometheus_service.list_metrics(match)
        return metrics
    except Exception as e:
        logger.error(f"Failed to list Prometheus metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list Prometheus metrics: {str(e)}",
        )


@router.get("/metadata", response_model=Dict[str, MetricResponse], summary="Get Metric Metadata")
async def get_metric_metadata(
    metric: Optional[str] = Query(
        None, description="Metric name to retrieve metadata for"),
    prometheus_service: PrometheusService = Depends(),
) -> Dict[str, MetricResponse]:
    """
    Get metadata about metrics in Prometheus.

    Args:
        metric: Optional metric name to filter metadata

    Returns:
        Dict[str, MetricResponse]: Metric metadata
    """
    try:
        metadata = await prometheus_service.get_metadata(metric)
        return metadata
    except Exception as e:
        logger.error(f"Failed to get Prometheus metric metadata: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get Prometheus metric metadata: {str(e)}",
        )
