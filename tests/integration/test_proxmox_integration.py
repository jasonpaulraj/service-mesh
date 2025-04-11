"""
Integration tests for Proxmox API integration.
These tests are meant to run against a real Proxmox instance.
Skip them in CI unless a test instance is available.
"""
import os
import pytest

from app.config import Settings
from app.models.proxmox import VMCreate
from app.services.proxmox_service import ProxmoxService


# Check if we have environment variables for the test
# If not, we'll skip these tests
skip_if_no_proxmox = pytest.mark.skipif(
    not (os.environ.get("TEST_PROXMOX_URL") and 
         os.environ.get("TEST_PROXMOX_USERNAME") and 
         os.environ.get("TEST_PROXMOX_PASSWORD")),
    reason="No Proxmox test credentials provided"
)


@pytest.fixture
def proxmox_service():
    """Create real Proxmox service for integration testing."""
    service = ProxmoxService(
        settings=Settings(
            PROXMOX_URL=os.environ.get("TEST_PROXMOX_URL", ""),
            PROXMOX_USERNAME=os.environ.get("TEST_PROXMOX_USERNAME", ""),
            PROXMOX_PASSWORD=os.environ.get("TEST_PROXMOX_PASSWORD", ""),
            PROXMOX_VERIFY_SSL=os.environ.get("TEST_PROXMOX_VERIFY_SSL", "False").lower() == "true"
        )
    )
    yield service


@skip_if_no_proxmox
@pytest.mark.asyncio
async def test_check_health(proxmox_service):
    """Test health check against real Proxmox instance."""
    result = await proxmox_service.check_health()
    assert result is True


@skip_if_no_proxmox
@pytest.mark.asyncio
async def test_get_nodes(proxmox_service):
    """Test retrieving nodes from real Proxmox instance."""
    nodes = await proxmox_service.get_nodes()
    
    assert isinstance(nodes, list)
    assert len(nodes) > 0
    assert all(hasattr(node, "node") for node in nodes)


@skip_if_no_proxmox
@pytest.mark.asyncio
async def test_get_cluster_overview(proxmox_service):
    """Test retrieving cluster overview from real Proxmox instance."""
    overview = await proxmox_service.get_cluster_overview()
    
    assert overview.nodes > 0
    assert hasattr(overview, "total_cpu")
    assert hasattr(overview, "total_memory")
    assert hasattr(overview, "total_disk")


@skip_if_no_proxmox
@pytest.mark.asyncio
async def test_get_vms(proxmox_service):
    """Test retrieving VMs from real Proxmox instance."""
    vms = await proxmox_service.get_vms()
    
    assert isinstance(vms, list)
    # There might be no VMs, but the structure should be correct
    for vm in vms:
        assert hasattr(vm, "vmid")
        assert hasattr(vm, "name")
        assert hasattr(vm, "status")
        assert hasattr(vm, "node")


@skip_if_no_proxmox
@pytest.mark.asyncio
async def test_get_specific_node(proxmox_service):
    """Test retrieving a specific node from real Proxmox instance."""
    # First get list of nodes
    nodes = await proxmox_service.get_nodes()
    if not nodes:
        pytest.skip("No nodes available for testing")
    
    # Get the first node
    first_node_name = nodes[0].node
    node = await proxmox_service.get_node(first_node_name)
    
    assert node is not None
    assert node.node == first_node_name


@skip_if_no_proxmox
@pytest.mark.asyncio
async def test_node_vms(proxmox_service):
    """Test retrieving VMs for a specific node from real Proxmox instance."""
    # First get list of nodes
    nodes = await proxmox_service.get_nodes()
    if not nodes:
        pytest.skip("No nodes available for testing")
    
    # Get VMs for the first node
    first_node_name = nodes[0].node
    vms = await proxmox_service.get_vms(node=first_node_name)
    
    assert isinstance(vms, list)
    # All VMs should be from the specified node
    for vm in vms:
        assert vm.node == first_node_name
