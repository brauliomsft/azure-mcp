from azure_clients import network_client, resource_client
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()
LOCATION = os.getenv("AZURE_LOCATION")
RESOURCE_GROUP = os.getenv("AZURE_RESOURCE_GROUP")

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

    network_client.virtual_networks.begin_create_or_update(
        RESOURCE_GROUP,
        vnet_name,
        {
            "location": LOCATION,
            "address_space": {"address_prefixes": ["10.0.0.0/16"]}
        },
    ).result()

    subnet = network_client.subnets.begin_create_or_update(
        RESOURCE_GROUP,
        vnet_name,
        subnet_name,
        {"address_prefix": "10.0.0.0/24"},
    ).result()

    public_ip = network_client.public_ip_addresses.begin_create_or_update(
        RESOURCE_GROUP,
        ip_name,
        {
            "location": LOCATION,
            "public_ip_allocation_method": "Dynamic"
        },
    ).result()

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