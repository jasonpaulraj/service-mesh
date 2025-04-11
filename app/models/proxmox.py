"""
Models for Proxmox API integration.
"""
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field


class ClusterNodeBase(BaseModel):
    """Base model for cluster node data."""
    
    node: str = Field(..., description="Name of the node")


class ClusterNodeRead(ClusterNodeBase):
    """Model for reading cluster node data."""
    
    id: str = Field(..., description="ID of the node")
    status: str = Field(..., description="Status of the node")
    cpu: Optional[float] = Field(None, description="CPU usage")
    memory: Optional[int] = Field(None, description="Memory usage in bytes")
    uptime: Optional[int] = Field(None, description="Uptime in seconds")
    ip: Optional[str] = Field(None, description="IP address of the node")


class NodesList(BaseModel):
    """Model for a list of nodes."""
    
    nodes: List[ClusterNodeRead] = Field(..., description="List of nodes")


class ClusterOverview(BaseModel):
    """Model for cluster overview data."""
    
    nodes: int = Field(..., description="Number of nodes")
    vms: int = Field(..., description="Number of VMs")
    storage: int = Field(..., description="Number of storage points")
    total_cpu: float = Field(..., description="Total CPU cores")
    total_memory: int = Field(..., description="Total memory in bytes")
    total_disk: int = Field(..., description="Total disk space in bytes")


class VMBase(BaseModel):
    """Base model for VM data."""
    
    name: str = Field(..., description="Name of the VM")


class VMCreate(VMBase):
    """Model for creating a new VM."""
    
    vmid: Optional[int] = Field(None, description="ID of the VM")
    cores: int = Field(..., description="Number of CPU cores")
    memory: int = Field(..., description="Memory in MB")
    disk: Optional[str] = Field(None, description="Disk configuration")
    net0: Optional[str] = Field(None, description="Network configuration")
    ostype: Optional[str] = Field("other", description="OS type")
    storage: str = Field(..., description="Storage for VM disks")
    iso: Optional[str] = Field(None, description="ISO file to use")


class VMRead(VMBase):
    """Model for reading VM data."""
    
    vmid: int = Field(..., description="ID of the VM")
    status: str = Field(..., description="Status of the VM")
    node: str = Field(..., description="Node where the VM is located")
    cpu: Optional[float] = Field(None, description="CPU usage")
    memory: Optional[int] = Field(None, description="Memory usage in bytes")
    disk: Optional[int] = Field(None, description="Disk usage in bytes")
    uptime: Optional[int] = Field(None, description="Uptime in seconds")


class VMsList(BaseModel):
    """Model for a list of VMs."""
    
    vms: List[VMRead] = Field(..., description="List of VMs")
