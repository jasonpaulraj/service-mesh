"""
Models for Grafana API integration.
"""
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class DashboardBase(BaseModel):
    """Base model for dashboard data."""
    
    title: str = Field(..., description="Title of the dashboard")


class DashboardCreate(BaseModel):
    """Model for creating a new dashboard."""
    
    dashboard_json: Dict[str, Any] = Field(..., description="Dashboard JSON definition")
    folder_id: Optional[int] = Field(0, description="Folder ID to save the dashboard in")
    overwrite: Optional[bool] = Field(False, description="Whether to overwrite existing dashboard")
    message: Optional[str] = Field("Dashboard created via API", description="Commit message")


class DashboardRead(DashboardBase):
    """Model for reading dashboard data."""
    
    id: Optional[int] = Field(None, description="ID of the dashboard")
    uid: str = Field(..., description="UID of the dashboard")
    url: str = Field(..., description="URL of the dashboard")
    folder_id: Optional[int] = Field(None, description="Folder ID of the dashboard")
    folder_title: Optional[str] = Field(None, description="Folder title of the dashboard")
    is_starred: Optional[bool] = Field(False, description="Whether the dashboard is starred")
    tags: Optional[List[str]] = Field([], description="Tags of the dashboard")


class DashboardsList(BaseModel):
    """Model for a list of dashboards."""
    
    dashboards: List[DashboardRead] = Field(..., description="List of dashboards")


class FolderBase(BaseModel):
    """Base model for folder data."""
    
    title: str = Field(..., description="Title of the folder")


class FolderCreate(FolderBase):
    """Model for creating a new folder."""
    
    pass


class FolderRead(FolderBase):
    """Model for reading folder data."""
    
    id: int = Field(..., description="ID of the folder")
    uid: str = Field(..., description="UID of the folder")
    url: str = Field(..., description="URL of the folder")


class FoldersList(BaseModel):
    """Model for a list of folders."""
    
    folders: List[FolderRead] = Field(..., description="List of folders")


class DataSourceBase(BaseModel):
    """Base model for data source data."""
    
    name: str = Field(..., description="Name of the data source")
    type: str = Field(..., description="Type of the data source")
    url: str = Field(..., description="URL of the data source")


class DataSourceCreate(DataSourceBase):
    """Model for creating a new data source."""
    
    access: str = Field("proxy", description="Access mode (proxy or direct)")
    is_default: Optional[bool] = Field(False, description="Whether the data source is default")
    basic_auth: Optional[bool] = Field(False, description="Whether to use basic auth")
    basic_auth_user: Optional[str] = Field(None, description="Basic auth username")
    basic_auth_password: Optional[str] = Field(None, description="Basic auth password")
    with_credentials: Optional[bool] = Field(False, description="Whether to send credentials")
    json_data: Optional[Dict[str, Any]] = Field(None, description="JSON data for the data source")
    secure_json_data: Optional[Dict[str, Any]] = Field(None, description="Secure JSON data for the data source")


class DataSourceRead(DataSourceBase):
    """Model for reading data source data."""
    
    id: int = Field(..., description="ID of the data source")
    uid: Optional[str] = Field(None, description="UID of the data source")
    access: str = Field(..., description="Access mode (proxy or direct)")
    is_default: bool = Field(..., description="Whether the data source is default")


class DataSourcesList(BaseModel):
    """Model for a list of data sources."""
    
    datasources: List[DataSourceRead] = Field(..., description="List of data sources")
