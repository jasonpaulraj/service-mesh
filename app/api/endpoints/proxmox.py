"""
Endpoints for integrating with Proxmox API.
"""
import logging
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from app.models.proxmox import (
    ClusterNodeRead,
    ClusterOverview,
    NodesList,
    VMCreate,
    VMRead,
    VMsList,
)
from app.services.proxmox_service import ProxmoxService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/nodes", response_model=NodesList, summary="Get All Nodes")
async def get_nodes(
    proxmox_service: ProxmoxService = Depends(),
) -> NodesList:
    """
    Retrieve all nodes from Proxmox cluster.

    Returns:
        NodesList: List of nodes
    """
    try:
        nodes = await proxmox_service.get_nodes()
        return NodesList(nodes=nodes)
    except Exception as e:
        logger.error(f"Failed to get Proxmox nodes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get Proxmox nodes: {str(e)}",
        )


@router.get("/nodes/{node}", response_model=ClusterNodeRead, summary="Get Node Details")
async def get_node(
    node: str = Path(..., description="The ID of the node to retrieve"),
    proxmox_service: ProxmoxService = Depends(),
) -> ClusterNodeRead:
    """
    Retrieve a specific node's details.

    Args:
        node: ID of the node to retrieve

    Returns:
        ClusterNodeRead: Node details
    """
    try:
        node_data = await proxmox_service.get_node(node)
        if not node_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Node {node} not found",
            )
        return node_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get node {node}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get node: {str(e)}",
        )


@router.get("/cluster", response_model=ClusterOverview, summary="Get Cluster Overview")
async def get_cluster_overview(
    proxmox_service: ProxmoxService = Depends(),
) -> ClusterOverview:
    """
    Retrieve an overview of the Proxmox cluster.

    Returns:
        ClusterOverview: Cluster overview data
    """
    try:
        overview = await proxmox_service.get_cluster_overview()
        return overview
    except Exception as e:
        logger.error(f"Failed to get cluster overview: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cluster overview: {str(e)}",
        )


@router.get("/vms", response_model=VMsList, summary="Get All VMs")
async def get_vms(
    node: Optional[str] = Query(None, description="Filter VMs by node"),
    proxmox_service: ProxmoxService = Depends(),
) -> VMsList:
    """
    Retrieve all virtual machines from Proxmox.

    Args:
        node: Optional node ID to filter VMs

    Returns:
        VMsList: List of virtual machines
    """
    try:
        vms = await proxmox_service.get_vms(node)
        return VMsList(vms=vms)
    except Exception as e:
        logger.error(f"Failed to get VMs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get VMs: {str(e)}",
        )


@router.get("/vms/{node}/{vmid}", response_model=VMRead, summary="Get VM Details")
async def get_vm(
    node: str = Path(..., description="The node where the VM is located"),
    vmid: int = Path(..., description="The ID of the VM to retrieve"),
    proxmox_service: ProxmoxService = Depends(),
) -> VMRead:
    """
    Retrieve a specific VM's details.

    Args:
        node: Node where the VM is located
        vmid: ID of the VM to retrieve

    Returns:
        VMRead: VM details
    """
    try:
        vm = await proxmox_service.get_vm(node, vmid)
        if not vm:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"VM with ID {vmid} not found on node {node}",
            )
        return vm
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get VM {vmid} on node {node}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get VM: {str(e)}",
        )


@router.post("/vms/{node}", response_model=VMRead, status_code=status.HTTP_201_CREATED, summary="Create VM")
async def create_vm(
    vm: VMCreate,
    node: str = Path(..., description="The node where to create the VM"),
    proxmox_service: ProxmoxService = Depends(),
) -> VMRead:
    """
    Create a new VM on a specific node.

    Args:
        node: Node where to create the VM
        vm: VM details to create

    Returns:
        VMRead: Created VM details
    """
    try:
        new_vm = await proxmox_service.create_vm(node, vm)
        return new_vm
    except Exception as e:
        logger.error(f"Failed to create VM on node {node}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create VM: {str(e)}",
        )


@router.post("/vms/{node}/{vmid}/start", response_model=Dict[str, str], summary="Start VM")
async def start_vm(
    node: str = Path(..., description="The node where the VM is located"),
    vmid: int = Path(..., description="The ID of the VM to start"),
    proxmox_service: ProxmoxService = Depends(),
) -> Dict[str, str]:
    """
    Start a VM.

    Args:
        node: Node where the VM is located
        vmid: ID of the VM to start

    Returns:
        Dict[str, str]: Operation result
    """
    try:
        result = await proxmox_service.start_vm(node, vmid)
        return {"status": "success", "message": result}
    except Exception as e:
        logger.error(f"Failed to start VM {vmid} on node {node}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start VM: {str(e)}",
        )


@router.post("/vms/{node}/{vmid}/stop", response_model=Dict[str, str], summary="Stop VM")
async def stop_vm(
    node: str = Path(..., description="The node where the VM is located"),
    vmid: int = Path(..., description="The ID of the VM to stop"),
    proxmox_service: ProxmoxService = Depends(),
) -> Dict[str, str]:
    """
    Stop a VM.

    Args:
        node: Node where the VM is located
        vmid: ID of the VM to stop

    Returns:
        Dict[str, str]: Operation result
    """
    try:
        result = await proxmox_service.stop_vm(node, vmid)
        return {"status": "success", "message": result}
    except Exception as e:
        logger.error(f"Failed to stop VM {vmid} on node {node}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop VM: {str(e)}",
        )


@router.delete("/vms/{node}/{vmid}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete VM")
async def delete_vm(
    node: str = Path(..., description="The node where the VM is located"),
    vmid: int = Path(..., description="The ID of the VM to delete"),
    proxmox_service: ProxmoxService = Depends(),
) -> None:
    """
    Delete a VM from Proxmox.

    Args:
        node: Node where the VM is located
        vmid: ID of the VM to delete
    """
    try:
        success = await proxmox_service.delete_vm(node, vmid)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"VM with ID {vmid} not found on node {node}",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete VM {vmid} on node {node}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete VM: {str(e)}",
        )
