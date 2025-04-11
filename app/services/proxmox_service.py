"""
Service for interacting with the Proxmox API.
"""
import logging
import time
from typing import Dict, List, Optional, Union

from fastapi import Depends
from proxmoxer import ProxmoxAPI

from app.config import Settings, get_settings
from app.models.proxmox import (
    ClusterNodeRead,
    ClusterOverview,
    VMCreate,
    VMRead,
)

logger = logging.getLogger(__name__)


class ProxmoxService:
    
    def __init__(self, settings: Settings = Depends(get_settings)):
        self.settings = settings
        self.client = None
        self._cache = {}
        self._cache_timestamp = {}
        self._cache_duration = 300  # Default cache duration: 5 minutes
    
    async def _get_client(self) -> ProxmoxAPI:
        if self.client is None:
            proxmox_host = self.settings.PROXMOX_URL
            if proxmox_host.startswith('http://') or proxmox_host.startswith('https://'):
                from urllib.parse import urlparse
                parsed_url = urlparse(proxmox_host)
                proxmox_host = parsed_url.netloc.split(':')[0]
            
            logger.debug(f"Connecting to Proxmox at {proxmox_host}")
            
            self.client = ProxmoxAPI(
                host=proxmox_host,
                user=self.settings.PROXMOX_USERNAME,
                password=self.settings.PROXMOX_PASSWORD,
                verify_ssl=self.settings.PROXMOX_VERIFY_SSL,
            )
            logger.info(f"Connected to Proxmox API at {self.settings.PROXMOX_URL}")
        return self.client
    
    async def check_health(self) -> bool:
        client = await self._get_client()
        try:
            version = client.version.get()
            logger.debug(f"Proxmox health check: {version}")
            return True
        except Exception as e:
            logger.error(f"Proxmox health check failed: {str(e)}")
            raise
    
    async def get_nodes(self) -> List[ClusterNodeRead]:
        """
        Get all nodes from the Proxmox cluster with caching.
        
        Returns:
            List[ClusterNodeRead]: List of nodes
        """
        client = await self._get_client()
        try:
            # Use caching for nodes data
            cache_key = 'nodes'
            
            # Check if we have cached data
            current_time = time.time()
            if (cache_key in self._cache and 
                cache_key in self._cache_timestamp and 
                current_time - self._cache_timestamp.get(cache_key, 0) <= self._cache_duration):
                logger.info(f"Using cached data for {cache_key} (age: {int(current_time - self._cache_timestamp[cache_key])}s)")
                return self._cache[cache_key]
            
            # Get all nodes
            nodes = client.nodes.get()
            logger.debug(f"Retrieved {len(nodes)} nodes from Proxmox")
            
            # Convert to our model format
            result = []
            for node in nodes:
                result.append(ClusterNodeRead(
                    id=node.get("id"),
                    node=node.get("node"),
                    status=node.get("status"),
                    cpu=node.get("cpu"),
                    memory=node.get("mem"),
                    uptime=node.get("uptime"),
                    ip=node.get("ip", ""),
                ))
            
            # Cache the result
            self._cache[cache_key] = result
            self._cache_timestamp[cache_key] = current_time
            logger.info(f"Updated cache for {cache_key}")
            
            return result
        except Exception as e:
            logger.error(f"Failed to get nodes: {str(e)}")
            raise
    
    async def get_node(self, node: str) -> Optional[ClusterNodeRead]:
        """
        Get a specific node's details.
        
        Args:
            node: ID of the node to retrieve
            
        Returns:
            Optional[ClusterNodeRead]: Node details or None if not found
        """
        client = await self._get_client()
        try:
            # Check if node exists
            nodes = client.nodes.get()
            node_exists = any(n.get("node") == node for n in nodes)
            if not node_exists:
                logger.warning(f"Node {node} not found")
                return None
            
            # Get node status
            status = client.nodes(node).status.get()
            logger.debug(f"Retrieved node {node} details from Proxmox")
            
            return ClusterNodeRead(
                id=node,
                node=node,
                status=status.get("status"),
                cpu=status.get("cpu"),
                memory=status.get("memory", {}).get("used"),
                uptime=status.get("uptime"),
                ip=status.get("ip", ""),
            )
        except Exception as e:
            logger.error(f"Failed to get node {node}: {str(e)}")
            raise
    
    async def get_cluster_overview(self) -> ClusterOverview:
        """
        Get an overview of the Proxmox cluster with caching.
        
        Returns:
            ClusterOverview: Cluster overview data
        """
        client = await self._get_client()
        try:
            # Use caching for cluster overview
            cache_key = 'cluster_overview'
            
            # Check if we have cached data
            current_time = time.time()
            if (cache_key in self._cache and 
                cache_key in self._cache_timestamp and 
                current_time - self._cache_timestamp.get(cache_key, 0) <= self._cache_duration):
                logger.info(f"Using cached data for {cache_key} (age: {int(current_time - self._cache_timestamp[cache_key])}s)")
                return self._cache[cache_key]
            
            # Get cluster resources
            resources = client.cluster.resources.get()
            
            # Count VMs, storage and nodes
            vm_count = sum(1 for r in resources if r.get("type") in ["qemu", "lxc"])
            storage_count = sum(1 for r in resources if r.get("type") == "storage")
            node_count = sum(1 for r in resources if r.get("type") == "node")
            
            # Calculate total resources
            total_cpu = 0
            total_memory = 0
            total_disk = 0
            
            for resource in resources:
                if resource.get("type") == "node":
                    total_cpu += resource.get("maxcpu", 0)
                    total_memory += resource.get("maxmem", 0)
                elif resource.get("type") == "storage":
                    total_disk += resource.get("maxdisk", 0)
            
            logger.debug(f"Retrieved cluster overview from Proxmox")
            
            result = ClusterOverview(
                nodes=node_count,
                vms=vm_count,
                storage=storage_count,
                total_cpu=total_cpu,
                total_memory=total_memory,
                total_disk=total_disk,
            )
            
            # Cache the result
            self._cache[cache_key] = result
            self._cache_timestamp[cache_key] = current_time
            logger.info(f"Updated cache for {cache_key}")
            
            return result
        except Exception as e:
            logger.error(f"Failed to get cluster overview: {str(e)}")
            raise
    
    async def get_vms(self, node: Optional[str] = None) -> List[VMRead]:
        """
        Get all virtual machines.
        
        Args:
            node: Optional node ID to filter VMs
            
        Returns:
            List[VMRead]: List of virtual machines
        """
        client = await self._get_client()
        try:
            vms = []
            
            # If node is specified, get VMs for that node only
            if node:
                vm_list = client.nodes(node).qemu.get()
                for vm in vm_list:
                    vm["node"] = node
                vms.extend(vm_list)
            else:
                # Get all nodes and then get VMs for each node
                nodes = client.nodes.get()
                for n in nodes:
                    node_name = n.get("node")
                    vm_list = client.nodes(node_name).qemu.get()
                    for vm in vm_list:
                        vm["node"] = node_name
                    vms.extend(vm_list)
            
            logger.debug(f"Retrieved {len(vms)} VMs from Proxmox")
            
            # Convert to our model format
            result = []
            for vm in vms:
                result.append(VMRead(
                    vmid=vm.get("vmid"),
                    name=vm.get("name"),
                    status=vm.get("status"),
                    node=vm.get("node"),
                    cpu=vm.get("cpu", 0),
                    memory=vm.get("maxmem", 0),
                    disk=vm.get("maxdisk", 0),
                    uptime=vm.get("uptime", 0),
                ))
            
            return result
        except Exception as e:
            logger.error(f"Failed to get VMs: {str(e)}")
            raise
    
    async def get_vm(self, node: str, vmid: int) -> Optional[VMRead]:
        """
        Get a specific VM's details.
        
        Args:
            node: Node where the VM is located
            vmid: ID of the VM to retrieve
            
        Returns:
            Optional[VMRead]: VM details or None if not found
        """
        client = await self._get_client()
        try:
            # Check if VM exists
            try:
                config = client.nodes(node).qemu(vmid).config.get()
                status = client.nodes(node).qemu(vmid).status.current.get()
            except Exception:
                logger.warning(f"VM {vmid} not found on node {node}")
                return None
            
            logger.debug(f"Retrieved VM {vmid} details from Proxmox")
            
            return VMRead(
                vmid=vmid,
                name=config.get("name"),
                status=status.get("status"),
                node=node,
                cpu=status.get("cpus", 0),
                memory=status.get("maxmem", 0),
                disk=None,  # Not directly available in config/status
                uptime=status.get("uptime", 0),
            )
        except Exception as e:
            logger.error(f"Failed to get VM {vmid} on node {node}: {str(e)}")
            raise
    
    async def create_vm(self, node: str, vm: VMCreate) -> VMRead:
        """
        Create a new VM on a specific node.
        
        Args:
            node: Node where to create the VM
            vm: VM details to create
            
        Returns:
            VMRead: Created VM details
        """
        client = await self._get_client()
        try:
            # Prepare VM creation parameters
            params = vm.dict(exclude_unset=True)
            
            # Create VM
            vmid = client.nodes(node).qemu.post(**params)
            logger.info(f"Created VM with ID {vmid} on node {node}")
            
            # Return the created VM
            return await self.get_vm(node, vmid)
        except Exception as e:
            logger.error(f"Failed to create VM on node {node}: {str(e)}")
            raise
    
    async def start_vm(self, node: str, vmid: int) -> str:
        """
        Start a VM.
        
        Args:
            node: Node where the VM is located
            vmid: ID of the VM to start
            
        Returns:
            str: Operation result
        """
        client = await self._get_client()
        try:
            # Check if VM exists
            vm = await self.get_vm(node, vmid)
            if not vm:
                raise ValueError(f"VM {vmid} not found on node {node}")
            
            # Start VM
            result = client.nodes(node).qemu(vmid).status.start.post()
            logger.info(f"Started VM {vmid} on node {node}")
            
            return f"VM {vmid} start initiated"
        except Exception as e:
            logger.error(f"Failed to start VM {vmid} on node {node}: {str(e)}")
            raise
    
    async def stop_vm(self, node: str, vmid: int) -> str:
        """
        Stop a VM.
        
        Args:
            node: Node where the VM is located
            vmid: ID of the VM to stop
            
        Returns:
            str: Operation result
        """
        client = await self._get_client()
        try:
            # Check if VM exists
            vm = await self.get_vm(node, vmid)
            if not vm:
                raise ValueError(f"VM {vmid} not found on node {node}")
            
            # Stop VM
            result = client.nodes(node).qemu(vmid).status.stop.post()
            logger.info(f"Stopped VM {vmid} on node {node}")
            
            return f"VM {vmid} stop initiated"
        except Exception as e:
            logger.error(f"Failed to stop VM {vmid} on node {node}: {str(e)}")
            raise
    
    async def delete_vm(self, node: str, vmid: int) -> bool:
        """
        Delete a VM.
        
        Args:
            node: Node where the VM is located
            vmid: ID of the VM to delete
            
        Returns:
            bool: True if deleted successfully, False if not found
        """
        client = await self._get_client()
        try:
            # Check if VM exists
            vm = await self.get_vm(node, vmid)
            if not vm:
                logger.warning(f"VM {vmid} not found on node {node} for deletion")
                return False
            
            # Delete VM
            client.nodes(node).qemu(vmid).delete()
            logger.info(f"Deleted VM {vmid} on node {node}")
            
            return True
        except Exception as e:
            logger.error(f"Failed to delete VM {vmid} on node {node}: {str(e)}")
            raise
