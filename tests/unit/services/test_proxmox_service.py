"""
Unit tests for Proxmox service.
"""
import pytest
from unittest.mock import MagicMock, patch

from proxmoxer import ProxmoxAPI

from app.config import Settings
from app.models.proxmox import VMCreate
from app.services.proxmox_service import ProxmoxService


@pytest.fixture
def mock_proxmox_client():
    """Mock ProxmoxAPI client."""
    mock_client = MagicMock(spec=ProxmoxAPI)
    
    # Mock version endpoint
    mock_client.version = MagicMock()
    mock_client.version.get.return_value = {"version": "7.2-3", "release": "stable"}
    
    # Mock nodes endpoint
    mock_client.nodes = MagicMock()
    mock_client.nodes.get.return_value = [
        {
            "id": "node1",
            "node": "node1",
            "status": "online",
            "cpu": 0.1,
            "mem": 1073741824,
            "uptime": 3600,
            "ip": "192.168.1.1"
        }
    ]
    
    # Mock node methods
    mock_node = MagicMock()
    mock_node.status.get.return_value = {
        "status": "online",
        "cpu": 0.1,
        "memory": {"used": 1073741824},
        "uptime": 3600,
        "ip": "192.168.1.1"
    }
    
    # Mock node qemu methods
    mock_node.qemu.get.return_value = [
        {
            "vmid": 100,
            "name": "test-vm1",
            "status": "running",
            "cpu": 1,
            "maxmem": 1073741824,
            "maxdisk": 10737418240,
            "uptime": 3600
        }
    ]
    
    # Mock vm config and status
    mock_vm = MagicMock()
    mock_vm.config.get.return_value = {
        "name": "test-vm1",
        "cores": 1,
        "memory": 1024
    }
    mock_vm.status.current.get.return_value = {
        "status": "running",
        "cpus": 1,
        "maxmem": 1073741824,
        "uptime": 3600
    }
    
    # Mock vm operations
    mock_vm.status.start.post.return_value = {"status": "ok"}
    mock_vm.status.stop.post.return_value = {"status": "ok"}
    
    # Link mocks together using __call__ to simulate method chaining
    mock_node.qemu.__call__.return_value = mock_vm
    mock_client.nodes.__call__.return_value = mock_node
    
    # Mock cluster resources
    mock_client.cluster = MagicMock()
    mock_client.cluster.resources.get.return_value = [
        {
            "type": "node",
            "node": "node1",
            "maxcpu": 4,
            "maxmem": 8589934592
        },
        {
            "type": "storage",
            "storage": "local",
            "maxdisk": 107374182400
        },
        {
            "type": "qemu",
            "name": "test-vm1",
            "vmid": 100
        }
    ]
    
    return mock_client


@pytest.fixture
def proxmox_service(mock_proxmox_client):
    """Create Proxmox service with mocked client."""
    with patch("app.services.proxmox_service.ProxmoxAPI", return_value=mock_proxmox_client):
        service = ProxmoxService(
            settings=Settings(
                PROXMOX_URL="test-proxmox.example.com",
                PROXMOX_USERNAME="test-user",
                PROXMOX_PASSWORD="test-password",
                PROXMOX_VERIFY_SSL=False
            )
        )
        yield service


@pytest.mark.asyncio
async def test_check_health(proxmox_service, mock_proxmox_client):
    """Test health check."""
    result = await proxmox_service.check_health()
    
    assert result is True
    mock_proxmox_client.version.get.assert_called_once()


@pytest.mark.asyncio
async def test_get_nodes(proxmox_service, mock_proxmox_client):
    """Test retrieving nodes."""
    nodes = await proxmox_service.get_nodes()
    
    assert len(nodes) == 1
    assert nodes[0].id == "node1"
    assert nodes[0].node == "node1"
    assert nodes[0].status == "online"
    mock_proxmox_client.nodes.get.assert_called_once()


@pytest.mark.asyncio
async def test_get_node(proxmox_service, mock_proxmox_client):
    """Test retrieving a specific node."""
    node = await proxmox_service.get_node("node1")
    
    assert node is not None
    assert node.id == "node1"
    assert node.node == "node1"
    mock_proxmox_client.nodes.get.assert_called_once()
    mock_proxmox_client.nodes.assert_called_once_with("node1")


@pytest.mark.asyncio
async def test_get_node_not_found(proxmox_service, mock_proxmox_client):
    """Test retrieving a non-existent node."""
    # Make nodes.get return a list that doesn't include the requested node
    mock_proxmox_client.nodes.get.return_value = [{"node": "different-node"}]
    
    node = await proxmox_service.get_node("nonexistent")
    
    assert node is None
    mock_proxmox_client.nodes.get.assert_called_once()


@pytest.mark.asyncio
async def test_get_cluster_overview(proxmox_service, mock_proxmox_client):
    """Test retrieving cluster overview."""
    overview = await proxmox_service.get_cluster_overview()
    
    assert overview.nodes == 1
    assert overview.vms == 1
    assert overview.storage == 1
    assert overview.total_cpu == 4
    assert overview.total_memory == 8589934592
    assert overview.total_disk == 107374182400
    mock_proxmox_client.cluster.resources.get.assert_called_once()


@pytest.mark.asyncio
async def test_get_vms(proxmox_service, mock_proxmox_client):
    """Test retrieving all VMs."""
    vms = await proxmox_service.get_vms()
    
    assert len(vms) == 1
    assert vms[0].vmid == 100
    assert vms[0].name == "test-vm1"
    assert vms[0].status == "running"
    mock_proxmox_client.nodes.get.assert_called_once()
    mock_proxmox_client.nodes.assert_called_once_with("node1")


@pytest.mark.asyncio
async def test_get_vms_filtered_by_node(proxmox_service, mock_proxmox_client):
    """Test retrieving VMs filtered by node."""
    vms = await proxmox_service.get_vms(node="node1")
    
    assert len(vms) == 1
    assert vms[0].vmid == 100
    assert vms[0].name == "test-vm1"
    mock_proxmox_client.nodes.assert_called_once_with("node1")


@pytest.mark.asyncio
async def test_get_vm(proxmox_service, mock_proxmox_client):
    """Test retrieving a specific VM."""
    vm = await proxmox_service.get_vm("node1", 100)
    
    assert vm is not None
    assert vm.vmid == 100
    assert vm.name == "test-vm1"
    assert vm.status == "running"
    mock_proxmox_client.nodes.assert_called_with("node1")


@pytest.mark.asyncio
async def test_get_vm_not_found(proxmox_service, mock_proxmox_client):
    """Test retrieving a non-existent VM."""
    # Make config.get raise an exception to simulate VM not found
    mock_vm = MagicMock()
    mock_vm.config.get.side_effect = Exception("VM not found")
    mock_node = MagicMock()
    mock_node.qemu.__call__.return_value = mock_vm
    mock_proxmox_client.nodes.__call__.return_value = mock_node
    
    vm = await proxmox_service.get_vm("node1", 999)
    
    assert vm is None


@pytest.mark.asyncio
async def test_create_vm(proxmox_service, mock_proxmox_client):
    """Test creating a VM."""
    new_vm = VMCreate(
        name="new-vm",
        cores=2,
        memory=2048,
        storage="local"
    )
    
    # Mock the post method to return a vmid
    mock_node_qemu = MagicMock()
    mock_node_qemu.post.return_value = 102
    mock_proxmox_client.nodes.return_value.qemu = mock_node_qemu
    
    # Also mock get_vm to return details for the new VM
    proxmox_service.get_vm = MagicMock()
    proxmox_service.get_vm.return_value = {
        "vmid": 102,
        "name": "new-vm",
        "status": "stopped",
        "node": "node1",
        "cpu": 2,
        "memory": 2048 * 1024 * 1024,
        "disk": None,
        "uptime": 0
    }
    
    result = await proxmox_service.create_vm("node1", new_vm)
    
    mock_node_qemu.post.assert_called_once()
    proxmox_service.get_vm.assert_called_once_with("node1", 102)


@pytest.mark.asyncio
async def test_start_vm(proxmox_service, mock_proxmox_client):
    """Test starting a VM."""
    # Mock get_vm to return a valid VM
    proxmox_service.get_vm = MagicMock()
    proxmox_service.get_vm.return_value = {
        "vmid": 100,
        "name": "test-vm1",
        "status": "stopped",
        "node": "node1"
    }
    
    result = await proxmox_service.start_vm("node1", 100)
    
    assert "VM 100 start initiated" in result
    proxmox_service.get_vm.assert_called_once_with("node1", 100)
    mock_proxmox_client.nodes.assert_called_with("node1")


@pytest.mark.asyncio
async def test_start_vm_not_found(proxmox_service, mock_proxmox_client):
    """Test starting a non-existent VM."""
    # Mock get_vm to return None for VM not found
    proxmox_service.get_vm = MagicMock()
    proxmox_service.get_vm.return_value = None
    
    with pytest.raises(ValueError, match="VM 999 not found on node node1"):
        await proxmox_service.start_vm("node1", 999)
    
    proxmox_service.get_vm.assert_called_once_with("node1", 999)


@pytest.mark.asyncio
async def test_stop_vm(proxmox_service, mock_proxmox_client):
    """Test stopping a VM."""
    # Mock get_vm to return a valid VM
    proxmox_service.get_vm = MagicMock()
    proxmox_service.get_vm.return_value = {
        "vmid": 100,
        "name": "test-vm1",
        "status": "running",
        "node": "node1"
    }
    
    result = await proxmox_service.stop_vm("node1", 100)
    
    assert "VM 100 stop initiated" in result
    proxmox_service.get_vm.assert_called_once_with("node1", 100)
    mock_proxmox_client.nodes.assert_called_with("node1")


@pytest.mark.asyncio
async def test_stop_vm_not_found(proxmox_service, mock_proxmox_client):
    """Test stopping a non-existent VM."""
    # Mock get_vm to return None for VM not found
    proxmox_service.get_vm = MagicMock()
    proxmox_service.get_vm.return_value = None
    
    with pytest.raises(ValueError, match="VM 999 not found on node node1"):
        await proxmox_service.stop_vm("node1", 999)
    
    proxmox_service.get_vm.assert_called_once_with("node1", 999)


@pytest.mark.asyncio
async def test_delete_vm(proxmox_service, mock_proxmox_client):
    """Test deleting a VM."""
    # Mock get_vm to return a valid VM
    proxmox_service.get_vm = MagicMock()
    proxmox_service.get_vm.return_value = {
        "vmid": 100,
        "name": "test-vm1",
        "status": "stopped",
        "node": "node1"
    }
    
    result = await proxmox_service.delete_vm("node1", 100)
    
    assert result is True
    proxmox_service.get_vm.assert_called_once_with("node1", 100)
    mock_proxmox_client.nodes.assert_called_with("node1")


@pytest.mark.asyncio
async def test_delete_vm_not_found(proxmox_service, mock_proxmox_client):
    """Test deleting a non-existent VM."""
    # Mock get_vm to return None for VM not found
    proxmox_service.get_vm = MagicMock()
    proxmox_service.get_vm.return_value = None
    
    result = await proxmox_service.delete_vm("node1", 999)
    
    assert result is False
    proxmox_service.get_vm.assert_called_once_with("node1", 999)
