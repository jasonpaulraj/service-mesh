"""
Endpoints for integrating with Grafana API.
"""
import logging
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from app.models.grafana import (
    DashboardCreate,
    DashboardRead,
    DashboardsList,
    DataSourceCreate,
    DataSourceRead,
    DataSourcesList,
    FolderCreate,
    FolderRead,
    FoldersList,
)
from app.services.grafana_service import GrafanaService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/dashboards", response_model=DashboardsList, summary="Get All Dashboards")
async def get_dashboards(
    folder_id: Optional[int] = Query(
        None, description="Filter dashboards by folder ID"),
    grafana_service: GrafanaService = Depends(),
) -> DashboardsList:
    """
    Retrieve all dashboards from Grafana.

    Args:
        folder_id: Optional folder ID to filter dashboards

    Returns:
        DashboardsList: List of dashboards
    """
    try:
        dashboards = await grafana_service.get_dashboards(folder_id)
        return DashboardsList(dashboards=dashboards)
    except Exception as e:
        logger.error(f"Failed to get dashboards: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dashboards: {str(e)}",
        )


@router.get("/dashboards/{dashboard_uid}", response_model=DashboardRead, summary="Get Dashboard by UID")
async def get_dashboard(
    dashboard_uid: str = Path(...,
                              description="The UID of the dashboard to retrieve"),
    grafana_service: GrafanaService = Depends(),
) -> DashboardRead:
    """
    Retrieve a specific dashboard by UID.

    Args:
        dashboard_uid: UID of the dashboard to retrieve

    Returns:
        DashboardRead: Dashboard details
    """
    try:
        dashboard = await grafana_service.get_dashboard(dashboard_uid)
        if not dashboard:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dashboard with UID {dashboard_uid} not found",
            )
        return dashboard
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get dashboard {dashboard_uid}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dashboard: {str(e)}",
        )


@router.post("/dashboards", response_model=DashboardRead, status_code=status.HTTP_201_CREATED, summary="Create Dashboard")
async def create_dashboard(
    dashboard: DashboardCreate,
    grafana_service: GrafanaService = Depends(),
) -> DashboardRead:
    """
    Create a new dashboard in Grafana.

    Args:
        dashboard: Dashboard details to create

    Returns:
        DashboardRead: Created dashboard details
    """
    try:
        new_dashboard = await grafana_service.create_dashboard(dashboard)
        return new_dashboard
    except Exception as e:
        logger.error(f"Failed to create dashboard: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create dashboard: {str(e)}",
        )


@router.delete("/dashboards/{dashboard_uid}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete Dashboard")
async def delete_dashboard(
    dashboard_uid: str = Path(...,
                              description="The UID of the dashboard to delete"),
    grafana_service: GrafanaService = Depends(),
) -> None:
    """
    Delete a dashboard from Grafana.

    Args:
        dashboard_uid: UID of the dashboard to delete
    """
    try:
        success = await grafana_service.delete_dashboard(dashboard_uid)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dashboard with UID {dashboard_uid} not found",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete dashboard {dashboard_uid}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete dashboard: {str(e)}",
        )


@router.get("/folders", response_model=FoldersList, summary="Get All Folders")
async def get_folders(
    grafana_service: GrafanaService = Depends(),
) -> FoldersList:
    """
    Retrieve all folders from Grafana.

    Returns:
        FoldersList: List of folders
    """
    try:
        folders = await grafana_service.get_folders()
        return FoldersList(folders=folders)
    except Exception as e:
        logger.error(f"Failed to get folders: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get folders: {str(e)}",
        )


@router.post("/folders", response_model=FolderRead, status_code=status.HTTP_201_CREATED, summary="Create Folder")
async def create_folder(
    folder: FolderCreate,
    grafana_service: GrafanaService = Depends(),
) -> FolderRead:
    """
    Create a new folder in Grafana.

    Args:
        folder: Folder details to create

    Returns:
        FolderRead: Created folder details
    """
    try:
        new_folder = await grafana_service.create_folder(folder)
        return new_folder
    except Exception as e:
        logger.error(f"Failed to create folder: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create folder: {str(e)}",
        )


@router.get("/datasources", response_model=DataSourcesList, summary="Get All Data Sources")
async def get_datasources(
    grafana_service: GrafanaService = Depends(),
) -> DataSourcesList:
    """
    Retrieve all data sources from Grafana.

    Returns:
        DataSourcesList: List of data sources
    """
    try:
        datasources = await grafana_service.get_datasources()
        return DataSourcesList(datasources=datasources)
    except Exception as e:
        logger.error(f"Failed to get data sources: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get data sources: {str(e)}",
        )


@router.post("/datasources", response_model=DataSourceRead, status_code=status.HTTP_201_CREATED, summary="Create Data Source")
async def create_datasource(
    datasource: DataSourceCreate,
    grafana_service: GrafanaService = Depends(),
) -> DataSourceRead:
    """
    Create a new data source in Grafana.

    Args:
        datasource: Data source details to create

    Returns:
        DataSourceRead: Created data source details
    """
    try:
        new_datasource = await grafana_service.create_datasource(datasource)
        return new_datasource
    except Exception as e:
        logger.error(f"Failed to create data source: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create data source: {str(e)}",
        )
