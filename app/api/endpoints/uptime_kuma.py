"""
Endpoints for integrating with Uptime Kuma.
"""
import logging
from typing import Dict, List, Optional
import json
import os
# Import Path from pathlib with an alias to avoid conflict
from pathlib import Path as FilePath

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from app.models.uptime_kuma import (
    MonitorCreate,
    MonitorRead,
    MonitorsList,
    MonitorUpdate,
    StatusPageRead,
    StatusPagesList,
)
from app.services.uptime_kuma_service import UptimeKumaService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/info", summary="Get Uptime Kuma Instance Info")
def get_info(
    uptime_kuma_service: UptimeKumaService = Depends(),
) -> dict:
    try:
        return uptime_kuma_service.get_info()
    except Exception as e:
        logger.error(f"Failed to get Uptime Kuma instance info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get instance info: {str(e)}",
        )


@router.get("/monitors", response_model=MonitorsList, summary="Get All Monitors")
def get_monitors(
    uptime_kuma_service: UptimeKumaService = Depends(),
) -> MonitorsList:
    try:
        monitors = uptime_kuma_service.get_monitors()
        return MonitorsList(monitors=monitors)
    except Exception as e:
        logger.error(f"Failed to get monitors: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get monitors: {str(e)}",
        )


@router.get(
    "/monitors/statistics",
    response_model=Dict,
    summary="Get Comprehensive Statistics for All Monitors",
    responses={
        200: {
            "description": "Successful Response",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "uptime_kuma_info": {
                                "type": "object",
                                "description": "Information about the Uptime Kuma instance"
                            },
                            "monitors": {
                                "type": "array",
                                "description": "List of monitors with detailed statistics"
                            }
                        }
                    },
                    "examples": {
                        "transformed": {
                            "summary": "Transformed statistics response",
                            "description": "Complete response with all monitors and their statistics",
                            "value": json.loads(FilePath(os.path.join(
                                os.path.dirname(os.path.dirname(
                                    os.path.dirname(os.path.dirname(__file__)))),
                                "dictionary", "uptime_kuma", "get_all_monitors_statistics", "response_transformed.json"
                            )).read_text(encoding="utf-8"))
                        },
                        "raw": {
                            "summary": "Raw statistics response",
                            "description": "Response with only essential monitor statistics",
                            "value": json.loads(FilePath(os.path.join(
                                os.path.dirname(os.path.dirname(
                                    os.path.dirname(os.path.dirname(__file__)))),
                                "dictionary", "uptime_kuma", "get_all_monitors_statistics", "response_raw.json"
                            )).read_text(encoding="utf-8"))
                        }
                    }
                }
            }
        }
    }
)
async def get_all_monitors_statistics(
    service: UptimeKumaService = Depends()
):
    """
    Get comprehensive statistics for all monitors.
    """
    return service.get_all_monitors_statistics()


@router.get("/monitors/{monitor_id}", response_model=MonitorRead, summary="Get Monitor by ID")
def get_monitor(
    monitor_id: int = Path(...,
                           description="The ID of the monitor to retrieve"),
    uptime_kuma_service: UptimeKumaService = Depends(),
) -> MonitorRead:
    try:
        monitor = uptime_kuma_service.get_monitor(monitor_id)
        if not monitor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Monitor with ID {monitor_id} not found",
            )
        return monitor
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get monitor {monitor_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get monitor: {str(e)}",
        )


@router.post("/monitors", response_model=MonitorRead, status_code=status.HTTP_201_CREATED, summary="Create Monitor")
def create_monitor(
    monitor: MonitorCreate,
    uptime_kuma_service: UptimeKumaService = Depends(),
) -> MonitorRead:
    try:
        new_monitor = uptime_kuma_service.create_monitor(monitor)
        return new_monitor
    except Exception as e:
        logger.error(f"Failed to create monitor: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create monitor: {str(e)}",
        )


@router.patch("/monitors/{monitor_id}", response_model=MonitorRead, summary="Update Monitor")
def update_monitor(
    monitor_update: MonitorUpdate,
    monitor_id: int = Path(..., description="The ID of the monitor to update"),
    uptime_kuma_service: UptimeKumaService = Depends(),
) -> MonitorRead:
    try:
        updated_monitor = uptime_kuma_service.update_monitor(
            monitor_id, monitor_update)
        if not updated_monitor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Monitor with ID {monitor_id} not found",
            )
        return updated_monitor
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update monitor {monitor_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update monitor: {str(e)}",
        )


@router.delete("/monitors/{monitor_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete Monitor")
def delete_monitor(
    monitor_id: int = Path(..., description="The ID of the monitor to delete"),
    uptime_kuma_service: UptimeKumaService = Depends(),
) -> None:
    try:
        success = uptime_kuma_service.delete_monitor(monitor_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Monitor with ID {monitor_id} not found",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete monitor {monitor_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete monitor: {str(e)}",
        )


@router.get("/monitors/{monitor_id}/avg-ping", summary="Get Average Ping for Monitor")
def get_avg_ping(
    monitor_id: int = Path(...,
                           description="The ID of the monitor to get average ping for"),
    uptime_kuma_service: UptimeKumaService = Depends(),
) -> Optional[float]:
    try:
        return uptime_kuma_service.get_avg_ping(monitor_id)
    except Exception as e:
        logger.error(
            f"Failed to get average ping for monitor {monitor_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get average ping: {str(e)}",
        )


@router.get("/monitors/{monitor_id}/cert-info", summary="Get Certificate Info for Monitor")
def get_cert_info(
    monitor_id: int = Path(...,
                           description="The ID of the monitor to get certificate info for"),
    uptime_kuma_service: UptimeKumaService = Depends(),
) -> Optional[dict]:
    try:
        return uptime_kuma_service.get_cert_info(monitor_id)
    except Exception as e:
        logger.error(
            f"Failed to get certificate info for monitor {monitor_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get certificate info: {str(e)}",
        )


@router.get("/monitors/{monitor_id}/uptime", summary="Get Uptime for Monitor")
def get_uptime(
    monitor_id: int = Path(...,
                           description="The ID of the monitor to get uptime for"),
    days: int = Query(
        7, description="Number of days to calculate uptime for", ge=1),
    uptime_kuma_service: UptimeKumaService = Depends(),
) -> Optional[float]:
    try:
        return uptime_kuma_service.get_uptime(monitor_id, days)
    except Exception as e:
        logger.error(
            f"Failed to get uptime for monitor {monitor_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get uptime: {str(e)}",
        )


@router.get("/monitors/{monitor_id}/statistics", summary="Get Comprehensive Statistics for Monitor")
def get_monitor_statistics(
    monitor_id: int = Path(...,
                           description="The ID of the monitor to get statistics for"),
    uptime_kuma_service: UptimeKumaService = Depends(),
) -> dict:
    try:
        return uptime_kuma_service.get_monitor_statistics(monitor_id)
    except Exception as e:
        logger.error(
            f"Failed to get statistics for monitor {monitor_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get monitor statistics: {str(e)}",
        )


@router.get("/status-pages", response_model=StatusPagesList, summary="Get All Status Pages")
def get_status_pages(
    uptime_kuma_service: UptimeKumaService = Depends(),
) -> StatusPagesList:
    try:
        status_pages = uptime_kuma_service.get_status_pages()
        return StatusPagesList(status_pages=status_pages)
    except Exception as e:
        logger.error(f"Failed to get status pages: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get status pages: {str(e)}",
        )


@router.get("/status-pages/{page_id}", response_model=StatusPageRead, summary="Get Status Page by ID")
def get_status_page(
    page_id: int = Path(...,
                        description="The ID of the status page to retrieve"),
    uptime_kuma_service: UptimeKumaService = Depends(),
) -> StatusPageRead:
    try:
        status_page = uptime_kuma_service.get_status_page(page_id)
        if not status_page:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Status page with ID {page_id} not found",
            )
        return status_page
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get status page {page_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get status page: {str(e)}",
        )
