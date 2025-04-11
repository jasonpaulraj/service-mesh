import logging
from typing import Dict, List, Optional, Union

from fastapi import Depends
from uptime_kuma_api import UptimeKumaApi

from app.config import Settings, get_settings
from app.models.uptime_kuma import (
    MonitorCreate,
    MonitorRead,
    MonitorUpdate,
    StatusPageRead,
)

logger = logging.getLogger(__name__)


class UptimeKumaService:

    def __init__(self, settings: Settings = Depends(get_settings)):
        self.settings = settings
        self.client = None

    def _get_client(self) -> UptimeKumaApi:
        if self.client is None:
            try:
                self.client = UptimeKumaApi(self.settings.UPTIME_KUMA_URL)
                self.client.login(
                    self.settings.UPTIME_KUMA_USERNAME,
                    self.settings.UPTIME_KUMA_PASSWORD
                )
            except Exception as e:
                logger.error(f"Connection to Uptime Kuma API failed: {str(e)}")
                self.client = None
                raise
        return self.client

    async def check_health(self) -> bool:
        try:
            client = UptimeKumaApi(self.settings.UPTIME_KUMA_URL)
            client.login(
                self.settings.UPTIME_KUMA_USERNAME,
                self.settings.UPTIME_KUMA_PASSWORD
            )
            logger.info("Uptime Kuma health check successful")
            logger.info(
                f"Connected to Uptime Kuma API at {self.settings.UPTIME_KUMA_URL}")
            client.disconnect()
            return True
        except Exception as e:
            logger.error(f"Uptime Kuma health check failed: {str(e)}")
            raise

    def get_monitors(self) -> List[MonitorRead]:
        client = self._get_client()
        try:
            monitors = client.get_monitors()
            logger.info(f"Retrieved {len(monitors)} monitors")
            return [MonitorRead(**monitor) for monitor in monitors]
        except Exception as e:
            logger.error(f"Failed to get monitors: {str(e)}")
            raise

    def get_monitor(self, monitor_id: int) -> Optional[MonitorRead]:
        client = self._get_client()
        try:
            monitor = client.get_monitor(monitor_id)
            if monitor:
                logger.info(f"Retrieved monitor {monitor_id}")
                return MonitorRead(**monitor)
            logger.warning(f"Monitor {monitor_id} not found")
            return None
        except Exception as e:
            logger.error(f"Failed to get monitor {monitor_id}: {str(e)}")
            raise

    def create_monitor(self, monitor: MonitorCreate) -> MonitorRead:
        client = self._get_client()
        try:
            created_monitor = client.add_monitor(**monitor.dict())
            logger.info(f"Created monitor {created_monitor['id']}")
            return MonitorRead(**created_monitor)
        except Exception as e:
            logger.error(f"Failed to create monitor: {str(e)}")
            raise

    def update_monitor(self, monitor_id: int, monitor: MonitorUpdate) -> Optional[MonitorRead]:
        client = self._get_client()
        try:
            existing_monitor = client.get_monitor(monitor_id)
            if not existing_monitor:
                logger.warning(f"Monitor {monitor_id} not found for update")
                return None

            update_data = monitor.dict(exclude_unset=True)
            updated_monitor = client.edit_monitor(monitor_id, **update_data)
            logger.info(f"Updated monitor {monitor_id}")
            return MonitorRead(**updated_monitor)
        except Exception as e:
            logger.error(f"Failed to update monitor {monitor_id}: {str(e)}")
            raise

    def delete_monitor(self, monitor_id: int) -> bool:
        client = self._get_client()
        try:
            existing_monitor = client.get_monitor(monitor_id)
            if not existing_monitor:
                logger.warning(f"Monitor {monitor_id} not found for deletion")
                return False

            client.delete_monitor(monitor_id)
            logger.info(f"Deleted monitor {monitor_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete monitor {monitor_id}: {str(e)}")
            raise

    def get_status_pages(self) -> List[StatusPageRead]:
        client = self._get_client()
        try:
            status_pages = client.get_status_pages()
            logger.info(f"Retrieved {len(status_pages)} status pages")
            return [StatusPageRead(**page) for page in status_pages]
        except Exception as e:
            logger.error(f"Failed to get status pages: {str(e)}")
            raise

    def get_status_page(self, page_id: int) -> Optional[StatusPageRead]:
        client = self._get_client()
        try:
            status_page = client.get_status_page(page_id)
            if status_page:
                logger.info(f"Retrieved status page {page_id}")
                return StatusPageRead(**status_page)
            logger.warning(f"Status page {page_id} not found")
            return None
        except Exception as e:
            logger.error(f"Failed to get status page {page_id}: {str(e)}")
            raise

    def close(self) -> None:
        if self.client:
            try:
                self.client.disconnect()
                logger.info("Closed Uptime Kuma API connection")
            except Exception as e:
                logger.error(
                    f"Error closing Uptime Kuma API connection: {str(e)}")
            finally:
                self.client = None

    def get_avg_ping(self, monitor_id: int) -> Optional[float]:
        client = self._get_client()
        try:
            avg_ping = client.avg_ping()
            if avg_ping is not None:
                logger.info(
                    f"Retrieved average ping for monitor {monitor_id}")
                return avg_ping
            logger.warning(
                f"Average ping not available for monitor {monitor_id}")
            return None
        except Exception as e:
            logger.error(
                f"Failed to get average ping for monitor {monitor_id}: {str(e)}")
            raise

    def get_cert_info(self, monitor_id: int) -> Optional[dict]:
        client = self._get_client()
        try:
            cert_info = client.cert_info()
            if cert_info:
                logger.info(
                    f"Retrieved certificate info for monitor {monitor_id}")
                return cert_info
            logger.warning(
                f"Certificate info not available for monitor {monitor_id}")
            return None
        except Exception as e:
            logger.error(
                f"Failed to get certificate info for monitor {monitor_id}: {str(e)}")
            raise

    def get_uptime(self, monitor_id: int, days: int = 7) -> Optional[float]:
        client = self._get_client()
        try:
            uptime = client.uptime(monitor_id, days)
            if uptime is not None:
                logger.info(
                    f"Retrieved uptime for monitor {monitor_id} over {days} days")
                return uptime
            logger.warning(f"Uptime not available for monitor {monitor_id}")
            return None
        except Exception as e:
            logger.error(
                f"Failed to get uptime for monitor {monitor_id}: {str(e)}")
            raise

    def get_info(self) -> dict:
        client = self._get_client()
        try:
            info = client.info()
            logger.info("Retrieved Uptime Kuma instance info")
            return info
        except Exception as e:
            logger.error(f"Failed to get Uptime Kuma instance info: {str(e)}")
            raise

    def get_monitor_statistics(self, monitor_id: int) -> dict:
        """
        Get comprehensive statistics for a monitor.

        Args:
            monitor_id: ID of the monitor to get statistics for

        Returns:
            dict: Dictionary containing various monitor statistics
        """
        client = self._get_client()
        try:
            monitor = client.get_monitor(monitor_id)

            all_avg_pings = client.avg_ping()
            all_uptimes = client.uptime()
            all_cert_infos = client.cert_info()
            all_heartbeats = client.get_heartbeats()
            all_important_heartbeats = client.get_important_heartbeats()

            stats = {
                'uptime_kuma_info': client.info(),
                'monitor': monitor,
                'avg_ping': all_avg_pings.get(monitor_id) if monitor_id in all_avg_pings else None,
                'uptime': all_uptimes.get(monitor_id),
                'cert_info': all_cert_infos.get(monitor_id),
                'heartbeats': all_heartbeats.get(monitor_id),
                'important_heartbeats': all_important_heartbeats.get(monitor_id),
            }

            logger.info(f"Retrieved statistics for monitor {monitor_id}")
            return stats
        except Exception as e:
            logger.error(
                f"Failed to get statistics for monitor {monitor_id}: {str(e)}")
            raise
            
    def get_all_monitors_statistics(self) -> dict:
        """
        Get comprehensive statistics for all monitors with caching.

        Returns:
            dict: Dictionary containing various statistics for all monitors
        """
        import time
        from app.resources.uptime_kuma import AllMonitorsStatisticsResource
        
        client = self._get_client()
        try:
            # Initialize cache attributes if they don't exist
            if not hasattr(self, '_cache') or not hasattr(self, '_cache_timestamp'):
                self._cache = {}
                self._cache_timestamp = {}
            
            # Cache duration in seconds (5 minutes)
            cache_duration = 300
            current_time = time.time()
            
            # Function to get or update cached data
            def get_cached_data(key, fetch_func):
                if (key not in self._cache or 
                    key not in self._cache_timestamp or 
                    current_time - self._cache_timestamp.get(key, 0) > cache_duration):
                    self._cache[key] = fetch_func()
                    self._cache_timestamp[key] = current_time
                    logger.info(f"Updated cache for {key}")
                else:
                    logger.info(f"Using cached data for {key} (age: {int(current_time - self._cache_timestamp[key])}s)")
                return self._cache[key]
            
            # Get all data with caching
            monitors = get_cached_data('monitors', client.get_monitors)
            info = get_cached_data('info', client.info)
            database_size = get_cached_data('database_size', client.get_database_size)
            avg_pings = get_cached_data('avg_pings', client.avg_ping)
            uptimes = get_cached_data('uptimes', client.uptime)
            cert_infos = get_cached_data('cert_infos', client.cert_info)
            heartbeats = get_cached_data('heartbeats', client.get_heartbeats)
            important_heartbeats = get_cached_data('important_heartbeats', client.get_important_heartbeats)
            
            # Compile statistics for all monitors
            raw_stats = {
                'uptime_kuma_info': {
                    **info,
                    'database_size': database_size,
                    'database_size_gb': round(database_size.get('size', 0) / (1024 * 1024 * 1024), 2) if isinstance(database_size, dict) else 0
                },
                'monitors': {}
            }
            
            # Process each monitor
            for monitor in monitors:
                monitor_id = monitor['id']
                raw_stats['monitors'][monitor_id] = {
                    'monitor': monitor,
                    'avg_ping': avg_pings.get(monitor_id),
                    'uptime': uptimes.get(monitor_id),
                    'cert_info': cert_infos.get(monitor_id),
                    'heartbeats': heartbeats.get(monitor_id),
                    'important_heartbeats': important_heartbeats.get(monitor_id),
                }
            
            stats = AllMonitorsStatisticsResource.transform(raw_stats)
            
            logger.info(f"Retrieved statistics for all monitors ({len(monitors)} total)")
            return stats
        except Exception as e:
            logger.error(f"Failed to get statistics for all monitors: {str(e)}")
            raise
