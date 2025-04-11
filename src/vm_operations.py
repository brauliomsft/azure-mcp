from mcp.server.fastmcp import FastMCP
from azure_clients import compute_client, network_client
from networking import ensure_resource_group, create_network_resources
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()
LOCATION = os.getenv("AZURE_LOCATION")
RESOURCE_GROUP = os.getenv("AZURE_RESOURCE_GROUP")

mcp = FastMCP("azure")

@mcp.tool()
def list_vms(rgname: str = RESOURCE_GROUP) -> None:
    """List all the VMs from an specified resources group and returns an array of VM names

    Args:
        vm_name: Name of the Virtual Machine to be created.
    """
    vm_names = []
    for vm in compute_client.virtual_machines.list(RESOURCE_GROUP):
        vm_names.append(vm.name)
    return vm_names

@mcp.tool()
def create_vm(vm_name: str) -> str:
    """Creates a Virtual Machine or VM in Azure based on a given name

    Args:
        vm_name: Name of the Virtual Machine to be created.
    """
    print(f"Creating VM: {vm_name}")
    ensure_resource_group()
    nic_id = create_network_resources(vm_name)

    vm_params = {
        "location": LOCATION,
        "storage_profile": {
            "image_reference": {
                "publisher": "Canonical",
                "offer": "UbuntuServer",
                "sku": "18.04-LTS",
                "version": "latest"
            }
        },
        "hardware_profile": {
            "vm_size": "Standard_B1s"
        },
        "os_profile": {
            "computer_name": vm_name,
            "admin_username": "azureuser",
            "admin_password": "Password1234!"  # ⚠️ Replace for production
        },
        "network_profile": {
            "network_interfaces": [{
                "id": nic_id,
                "primary": True
            }]
        }
    }

    async_vm_creation = compute_client.virtual_machines.begin_create_or_update(
        RESOURCE_GROUP, vm_name, vm_params
    )
    async_vm_creation.result()
    return "VM created successfully."

@mcp.tool()
def delete_vm(vm_name: str) -> str:
    print(f"Deleting VM: {vm_name}")
    compute_client.virtual_machines.begin_delete(RESOURCE_GROUP, vm_name).result()

    print("Cleaning up network resources...")
    nic_name = f"{vm_name}-nic"
    ip_name = f"{vm_name}-ip"
    vnet_name = f"{vm_name}-vnet"

    try:
        network_client.network_interfaces.begin_delete(RESOURCE_GROUP, nic_name).result()
        network_client.public_ip_addresses.begin_delete(RESOURCE_GROUP, ip_name).result()
        network_client.virtual_networks.begin_delete(RESOURCE_GROUP, vnet_name).result()
    except Exception as e:
        print(f"Warning: Some resources couldn't be deleted automatically: {e}")

    return "VM and network resources deleted."