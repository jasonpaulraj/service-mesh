"""
Models for Uptime Kuma API integration.
"""
from datetime import datetime
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field


class MonitorBase(BaseModel):
    """Base model for monitor data."""
    
    name: str = Field(..., description="Name of the monitor")
    type: str = Field(..., description="Type of the monitor (e.g., http, ping)")
    url: str = Field(..., description="URL to monitor")
    interval: int = Field(60, description="Check interval in seconds")


class MonitorCreate(MonitorBase):
    """Model for creating a new monitor."""
    
    description: Optional[str] = Field(None, description="Description of the monitor")
    retryInterval: Optional[int] = Field(None, description="Retry interval in seconds")
    maxretries: Optional[int] = Field(None, description="Maximum number of retries")
    active: Optional[bool] = Field(True, description="Whether the monitor is active")
    keyword: Optional[str] = Field(None, description="Keyword to search for in the response")
    expectStatus: Optional[int] = Field(None, description="Expected HTTP status code")


class MonitorUpdate(BaseModel):
    """Model for updating an existing monitor."""
    
    name: Optional[str] = Field(None, description="Name of the monitor")
    type: Optional[str] = Field(None, description="Type of the monitor (e.g., http, ping)")
    url: Optional[str] = Field(None, description="URL to monitor")
    interval: Optional[int] = Field(None, description="Check interval in seconds")
    description: Optional[str] = Field(None, description="Description of the monitor")
    retryInterval: Optional[int] = Field(None, description="Retry interval in seconds")
    maxretries: Optional[int] = Field(None, description="Maximum number of retries")
    active: Optional[bool] = Field(None, description="Whether the monitor is active")
    keyword: Optional[str] = Field(None, description="Keyword to search for in the response")
    expectStatus: Optional[int] = Field(None, description="Expected HTTP status code")


class MonitorRead(MonitorBase):
    """Model for reading monitor data."""
    
    id: int = Field(..., description="ID of the monitor")
    description: Optional[str] = Field(None, description="Description of the monitor")
    active: bool = Field(..., description="Whether the monitor is active")
    status: Optional[int] = Field(None, description="Status of the monitor")
    uptime: Optional[float] = Field(None, description="Uptime percentage")
    avgPing: Optional[float] = Field(None, description="Average ping time")
    lastCheck: Optional[datetime] = Field(None, description="Last check time")


class MonitorsList(BaseModel):
    """Model for a list of monitors."""
    
    monitors: List[MonitorRead] = Field(..., description="List of monitors")


class StatusPageBase(BaseModel):
    """Base model for status page data."""
    
    title: str = Field(..., description="Title of the status page")
    slug: str = Field(..., description="Slug of the status page")


class StatusPageRead(StatusPageBase):
    """Model for reading status page data."""
    
    id: int = Field(..., description="ID of the status page")
    description: Optional[str] = Field(None, description="Description of the status page")
    theme: Optional[str] = Field(None, description="Theme of the status page")
    published: bool = Field(..., description="Whether the status page is published")
    showTags: Optional[bool] = Field(None, description="Whether to show tags")
    domain: Optional[str] = Field(None, description="Custom domain for the status page")


class StatusPagesList(BaseModel):
    """Model for a list of status pages."""
    
    status_pages: List[StatusPageRead] = Field(..., description="List of status pages")


class SystemHealthResponse(BaseModel):
    """Model for system health response."""
    
    status: str = Field(..., description="Overall system health status")
    timestamp: datetime = Field(..., description="Timestamp of the health check")
    services: Dict[str, Dict[str, Optional[str]]] = Field(
        ..., description="Status of individual services"
    )
