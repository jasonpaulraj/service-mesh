"""
Models for Prometheus API integration.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class MetricDataPoint(BaseModel):
    """Model for a single metric data point."""
    
    timestamp: float = Field(..., description="Timestamp of the data point")
    value: Union[float, str] = Field(..., description="Value of the data point")


class MetricData(BaseModel):
    """Model for metric data."""
    
    metric: Dict[str, str] = Field(..., description="Metric labels")
    values: Optional[List[MetricDataPoint]] = Field(None, description="List of data points")
    value: Optional[MetricDataPoint] = Field(None, description="Single data point")


class QueryResult(BaseModel):
    """Model for Prometheus query result."""
    
    status: str = Field(..., description="Status of the query")
    data: Optional[List[Dict[str, Any]]] = Field(None, description="Query result data")


class MetricRange(BaseModel):
    """Model for Prometheus range query result."""
    
    status: str = Field(..., description="Status of the query")
    data: Optional[List[Dict[str, Any]]] = Field(None, description="Range query result data")


class Alert(BaseModel):
    """Model for Prometheus alert."""
    
    labels: Dict[str, str] = Field(..., description="Alert labels")
    annotations: Dict[str, str] = Field(..., description="Alert annotations")
    state: str = Field(..., description="Alert state")
    activeAt: Optional[datetime] = Field(None, description="When the alert became active")
    value: Optional[float] = Field(None, description="Alert value")


class AlertsResponse(BaseModel):
    """Model for Prometheus alerts response."""
    
    alerts: List[Dict[str, Any]] = Field(..., description="List of alerts")


class MetricResponse(BaseModel):
    """Model for Prometheus metric metadata."""
    
    type: str = Field(..., description="Metric type")
    help: str = Field(..., description="Metric help text")
    unit: Optional[str] = Field(None, description="Metric unit")
