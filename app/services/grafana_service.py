import logging
from typing import Dict, List, Optional, Union

from fastapi import Depends
from grafana_client import GrafanaApi

from app.config import Settings, get_settings
from app.models.grafana import (
    DashboardCreate,
    DashboardRead,
    DataSourceCreate,
    DataSourceRead,
    FolderCreate,
    FolderRead,
)

logger = logging.getLogger(__name__)


class GrafanaService:
    
    def __init__(self, settings: Settings = Depends(get_settings)):
        self.settings = settings
        self.client = None
    
    async def _get_client(self) -> GrafanaApi:
        if self.client is None:
            try:
                grafana_url = self.settings.GRAFANA_URL
                
                if grafana_url.startswith("http://"):
                    host = grafana_url.replace("http://", "")
                elif grafana_url.startswith("https://"):
                    host = grafana_url.replace("https://", "")
                else:
                    host = grafana_url
                
                protocol = "http" if grafana_url.startswith("http://") else "https"
                
                if hasattr(self.settings, 'GRAFANA_API_KEY') and self.settings.GRAFANA_API_KEY:
                    self.client = GrafanaApi(
                        host=host,
                        protocol=protocol,
                        api_key=self.settings.GRAFANA_API_KEY
                    )
                elif hasattr(self.settings, 'GRAFANA_USERNAME') and hasattr(self.settings, 'GRAFANA_PASSWORD'):
                    self.client = GrafanaApi(
                        host=host,
                        protocol=protocol,
                        auth=(self.settings.GRAFANA_USERNAME, self.settings.GRAFANA_PASSWORD)
                    )
                else:
                    self.client = GrafanaApi(host=host, protocol=protocol)
                
                logger.info(f"Connected to Grafana API at {protocol}://{host}")
            except Exception as e:
                logger.error(f"Connection to Grafana API failed: {str(e)}")
                raise
        return self.client
    
    async def check_health(self) -> bool:
        client = await self._get_client()
        try:
            health = client.health.check()
            logger.debug(f"Grafana health check: {health}")
            return True
        except Exception as e:
            logger.error(f"Grafana health check failed: {str(e)}")
            raise
    
    async def get_dashboards(self, folder_id: Optional[int] = None) -> List[DashboardRead]:
        client = await self._get_client()
        try:
            if folder_id is not None:
                dashboards = client.search.search_dashboards(folder_ids=[folder_id])
            else:
                dashboards = client.search.search_dashboards()
            
            logger.debug(f"Retrieved {len(dashboards)} dashboards")
            
            result = []
            for dashboard in dashboards:
                result.append(DashboardRead(
                    id=dashboard.get("id"),
                    uid=dashboard.get("uid"),
                    title=dashboard.get("title"),
                    url=dashboard.get("url"),
                    folder_id=dashboard.get("folderId"),
                    folder_title=dashboard.get("folderTitle"),
                    is_starred=dashboard.get("isStarred", False),
                    tags=dashboard.get("tags", []),
                ))
            
            return result
        except Exception as e:
            logger.error(f"Failed to get dashboards: {str(e)}")
            raise
    
    async def get_dashboard(self, dashboard_uid: str) -> Optional[DashboardRead]:
        client = await self._get_client()
        try:
            dashboard = client.dashboard.get_dashboard(dashboard_uid)
            if not dashboard:
                logger.warning(f"Dashboard {dashboard_uid} not found")
                return None
            
            meta = dashboard.get("meta", {})
            dashboard_data = dashboard.get("dashboard", {})
            
            logger.debug(f"Retrieved dashboard {dashboard_uid}")
            
            return DashboardRead(
                id=meta.get("id"),
                uid=dashboard_uid,
                title=dashboard_data.get("title"),
                url=f"/d/{dashboard_uid}",
                folder_id=meta.get("folderId"),
                folder_title=meta.get("folderTitle"),
                is_starred=meta.get("isStarred", False),
                tags=dashboard_data.get("tags", []),
            )
        except Exception as e:
            logger.error(f"Failed to get dashboard {dashboard_uid}: {str(e)}")
            raise
    
    async def create_dashboard(self, dashboard: DashboardCreate) -> DashboardRead:
        client = await self._get_client()
        try:
            dashboard_json = dashboard.dashboard_json
            payload = {
                "dashboard": dashboard_json,
                "folderId": dashboard.folder_id,
                "overwrite": dashboard.overwrite,
                "message": dashboard.message,
            }
            
            result = client.dashboard.update_dashboard(payload)
            logger.info(f"Created dashboard {result.get('uid')}")
            
            uid = result.get("uid")
            return await self.get_dashboard(uid)
        except Exception as e:
            logger.error(f"Failed to create dashboard: {str(e)}")
            raise
    
    async def delete_dashboard(self, dashboard_uid: str) -> bool:
        client = await self._get_client()
        try:
            dashboard = await self.get_dashboard(dashboard_uid)
            if not dashboard:
                logger.warning(f"Dashboard {dashboard_uid} not found for deletion")
                return False
            
            client.dashboard.delete_dashboard(dashboard_uid)
            logger.info(f"Deleted dashboard {dashboard_uid}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete dashboard {dashboard_uid}: {str(e)}")
            raise
    
    async def get_folders(self) -> List[FolderRead]:
        client = await self._get_client()
        try:
            folders = client.folder.get_all_folders()
            logger.debug(f"Retrieved {len(folders)} folders")
            
            result = []
            for folder in folders:
                result.append(FolderRead(
                    id=folder.get("id"),
                    uid=folder.get("uid"),
                    title=folder.get("title"),
                    url=folder.get("url"),
                ))
            
            return result
        except Exception as e:
            logger.error(f"Failed to get folders: {str(e)}")
            raise
    
    async def create_folder(self, folder: FolderCreate) -> FolderRead:
        client = await self._get_client()
        try:
            result = client.folder.create_folder(folder.title)
            logger.info(f"Created folder {result.get('uid')}")
            
            return FolderRead(
                id=result.get("id"),
                uid=result.get("uid"),
                title=result.get("title"),
                url=result.get("url"),
            )
        except Exception as e:
            logger.error(f"Failed to create folder: {str(e)}")
            raise
    
    async def get_datasources(self) -> List[DataSourceRead]:
        client = await self._get_client()
        try:
            datasources = client.datasource.list_datasources()
            logger.debug(f"Retrieved {len(datasources)} data sources")
            
            result = []
            for ds in datasources:
                result.append(DataSourceRead(
                    id=ds.get("id"),
                    uid=ds.get("uid"),
                    name=ds.get("name"),
                    type=ds.get("type"),
                    url=ds.get("url"),
                    access=ds.get("access"),
                    is_default=ds.get("isDefault", False),
                ))
            
            return result
        except Exception as e:
            logger.error(f"Failed to get data sources: {str(e)}")
            raise
    
    async def create_datasource(self, datasource: DataSourceCreate) -> DataSourceRead:
        client = await self._get_client()
        try:
            payload = datasource.dict(exclude_unset=True)
            
            result = client.datasource.create_datasource(payload)
            logger.info(f"Created data source {result.get('id')}")
            
            return DataSourceRead(
                id=result.get("datasource", {}).get("id"),
                uid=result.get("datasource", {}).get("uid"),
                name=datasource.name,
                type=datasource.type,
                url=datasource.url,
                access=datasource.access,
                is_default=datasource.is_default,
            )
        except Exception as e:
            logger.error(f"Failed to create data source: {str(e)}")
            raise
