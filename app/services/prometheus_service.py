"""
Service for interacting with the Prometheus API.
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional, Union

from fastapi import Depends
from prometheus_api_client import PrometheusConnect

from app.config import Settings, get_settings
from app.models.prometheus import (
    AlertsResponse,
    MetricRange,
    MetricResponse,
    QueryResult,
)

logger = logging.getLogger(__name__)


class PrometheusService:
    """Service for interacting with Prometheus API."""
    
    def __init__(self, settings: Settings = Depends(get_settings)):
        """
        Initialize the Prometheus service.
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        self.client = None
    
    async def _get_client(self) -> PrometheusConnect:
        """
        Get or create a Prometheus API client.
        
        Returns:
            PrometheusConnect: API client
        """
        if self.client is None:
            auth = None
            if self.settings.PROMETHEUS_USERNAME and self.settings.PROMETHEUS_PASSWORD:
                auth = (self.settings.PROMETHEUS_USERNAME, self.settings.PROMETHEUS_PASSWORD)
            
            self.client = PrometheusConnect(
                url=self.settings.PROMETHEUS_URL,
                disable_ssl=not self.settings.PROMETHEUS_URL.startswith("https"),
                headers={"User-Agent": "PrometheusIntegrationAPI/0.1.0"},
                auth=auth,
            )
            logger.info("Successfully connected to Prometheus API")
        return self.client
    
    async def check_health(self) -> bool:
        """
        Check if the Prometheus API is healthy.
        
        Returns:
            bool: True if the API is healthy
            
        Raises:
            Exception: If the API is not healthy
        """
        client = await self._get_client()
        try:
            # Use a simple query to check if Prometheus is up
            result = client.custom_query(query="up")
            logger.debug(f"Prometheus health check successful: {result}")
            return True
        except Exception as e:
            logger.error(f"Prometheus health check failed: {str(e)}")
            raise
    
    async def query(self, query: str, time: Optional[datetime] = None) -> QueryResult:
        """
        Execute a PromQL query.
        
        Args:
            query: PromQL query string
            time: Optional evaluation timestamp
            
        Returns:
            QueryResult: Query result data
        """
        client = await self._get_client()
        
        # Convert time to string format if provided
        timestamp = None
        if time:
            timestamp = time.timestamp()
        
        try:
            result = client.custom_query(query=query, time=timestamp)
            logger.debug(f"Executed Prometheus query: {query}")
            return QueryResult(
                status="success",
                data=result
            )
        except Exception as e:
            logger.error(f"Failed to execute Prometheus query {query}: {str(e)}")
            raise
    
    async def query_range(
        self, query: str, start: datetime, end: datetime, step: str
    ) -> MetricRange:
        """
        Execute a PromQL range query.
        
        Args:
            query: PromQL query string
            start: Start timestamp
            end: End timestamp
            step: Query resolution step width
            
        Returns:
            MetricRange: Range query result data
        """
        client = await self._get_client()
        
        # Convert timestamps to string format
        start_time = start.timestamp()
        end_time = end.timestamp()
        
        try:
            result = client.custom_query_range(
                query=query,
                start_time=start_time,
                end_time=end_time,
                step=step
            )
            logger.debug(f"Executed Prometheus range query: {query}")
            return MetricRange(
                status="success",
                data=result
            )
        except Exception as e:
            logger.error(f"Failed to execute Prometheus range query {query}: {str(e)}")
            raise
    
    async def get_alerts(self) -> AlertsResponse:
        """
        Get all active alerts.
        
        Returns:
            AlertsResponse: Active alerts data
        """
        client = await self._get_client()
        try:
            alerts = client.all_alerts()
            logger.debug(f"Retrieved {len(alerts)} alerts from Prometheus")
            return AlertsResponse(alerts=alerts)
        except Exception as e:
            logger.error(f"Failed to get Prometheus alerts: {str(e)}")
            raise
    
    async def list_metrics(self, match: Optional[str] = None) -> List[str]:
        """
        List available metrics.
        
        Args:
            match: Optional regex pattern to filter metrics
            
        Returns:
            List[str]: List of available metric names
        """
        client = await self._get_client()
        try:
            metrics = client.all_metrics(match)
            logger.debug(f"Retrieved {len(metrics)} metrics from Prometheus")
            return metrics
        except Exception as e:
            logger.error(f"Failed to list Prometheus metrics: {str(e)}")
            raise
    
    async def get_metadata(self, metric: Optional[str] = None) -> Dict[str, MetricResponse]:
        """
        Get metadata about metrics.
        
        Args:
            metric: Optional metric name to filter metadata
            
        Returns:
            Dict[str, MetricResponse]: Metric metadata
        """
        client = await self._get_client()
        try:
            metadata = client.get_metadata(metric)
            logger.debug(f"Retrieved metadata for Prometheus metrics")
            
            # Convert to our model format
            result = {}
            for key, value in metadata.items():
                result[key] = MetricResponse(
                    type=value.get("type", ""),
                    help=value.get("help", ""),
                    unit=value.get("unit", "")
                )
            
            return result
        except Exception as e:
            logger.error(f"Failed to get Prometheus metric metadata: {str(e)}")
            raise
