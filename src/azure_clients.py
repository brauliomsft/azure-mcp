from azure.identity import InteractiveBrowserCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.network import NetworkManagementClient
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Get subscription ID from environment variable
SUBSCRIPTION_ID = os.getenv('SUBSCRIPTION_ID')

credential = InteractiveBrowserCredential()

compute_client = ComputeManagementClient(credential, SUBSCRIPTION_ID)
resource_client = ResourceManagementClient(credential, SUBSCRIPTION_ID)
network_client = NetworkManagementClient(credential, SUBSCRIPTION_ID)
