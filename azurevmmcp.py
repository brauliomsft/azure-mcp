import argparse
from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP
from azure.identity import InteractiveBrowserCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.network import NetworkManagementClient

# Replace with your own values

RESOURCE_GROUP = "demoRG"
LOCATION = "westus2"

mcp = FastMCP("azure")

# Azure clients
credential = InteractiveBrowserCredential()
compute_client = ComputeManagementClient(credential, SUBSCRIPTION_ID)
resource_client = ResourceManagementClient(credential, SUBSCRIPTION_ID)
network_client = NetworkManagementClient(credential, SUBSCRIPTION_ID)

def ensure_resource_group():
    resource_client.resource_groups.create_or_update(
        RESOURCE_GROUP, {"location": LOCATION}
    )

def create_network_resources(vm_name):
    print("Creating network resources...")

    vnet_name = f"{vm_name}-vnet"
    subnet_name = f"{vm_name}-subnet"
    ip_name = f"{vm_name}-ip"
    nic_name = f"{vm_name}-nic"

    # Create VNet
    network_client.virtual_networks.begin_create_or_update(
        RESOURCE_GROUP,
        vnet_name,
        {
            "location": LOCATION,
            "address_space": {"address_prefixes": ["10.0.0.0/16"]}
        },
    ).result()

    # Create Subnet
    subnet = network_client.subnets.begin_create_or_update(
        RESOURCE_GROUP,
        vnet_name,
        subnet_name,
        {"address_prefix": "10.0.0.0/24"},
    ).result()

    # Create Public IP
    public_ip = network_client.public_ip_addresses.begin_create_or_update(
        RESOURCE_GROUP,
        ip_name,
        {
            "location": LOCATION,
            "public_ip_allocation_method": "Dynamic"
        },
    ).result()

    # Create NIC
    nic = network_client.network_interfaces.begin_create_or_update(
        RESOURCE_GROUP,
        nic_name,
        {
            "location": LOCATION,
            "ip_configurations": [{
                "name": f"{vm_name}-ipconfig",
                "subnet": {"id": subnet.id},
                "public_ip_address": {"id": public_ip.id}
            }]
        },
    ).result()

    return nic.id

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
    """Deletes a Virtual Machine or VM in Azure based on a given name

    Args:
        vm_name: Name of the Virtual Machine to be created.
    """
    compute_client.virtual_machines.begin_delete(RESOURCE_GROUP, vm_name).result()

    # Optionally delete network resources
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

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')