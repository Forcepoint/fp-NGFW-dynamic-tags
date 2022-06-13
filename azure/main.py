"""
Author: David LePage

Instructions were primarily derived from this site:

https://docs.microsoft.com/en-us/azure/developer/python/sdk/authentication-local-development-service-principal?tabs=azure-portal

Some additional useful information:

https://docs.microsoft.com/en-us/azure/developer/python/azure-sdk-authenticate-service-principals

The process of registering the application generates the client ID that will be required to interact with the
azure client SDKs.

https://docs.microsoft.com/en-us/azure/developer/python/configure-local-development-environment?tabs=cmd#create-a-service-principal-and-environment-variables-for-development

NOTE: This code uses environment variables for convenience instead of retrieving the values from another source such as Azure Storage or Azure Key Vault. 

EnvironmentCredential (the credential provider used) assumes that the following environment variables are set:
    AZURE_TENANT_ID
    AZURE_CLIENT_ID

Plus one of the following (which are attempted in this order):
    AZURE_CLIENT_SECRET
or:
    AZURE_CLIENT_CERTIFICATE_PATH
or:
    AZURE_USERNAME and AZURE_PASSWORD

"""
import os
import sys
import logging
import argparse
import functools
from typing import List
from pprint import pprint
from azure.mgmt.resource import SubscriptionClient
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.identity import EnvironmentCredential
from smc import session
from smc.elements.network import IPList
from dotenv import load_dotenv


logger = logging.getLogger(__name__)

def get_subscription_client(credential: EnvironmentCredential) -> SubscriptionClient:
    """
    Return a subscription client using the provided credential
    """
    return SubscriptionClient(credential)

def get_compute_client(credential: EnvironmentCredential, subscription_id: str) -> ComputeManagementClient:
    """
    Return a compute management client
    """
    return ComputeManagementClient(credential, subscription_id)

def get_network_management_client(credential: EnvironmentCredential, subscription_id: str) -> NetworkManagementClient:
    """
    Return a network management client
    """
    return NetworkManagementClient(credential, subscription_id)

def get_private_address(network_client: NetworkManagementClient, azure_resource_group: str, azure_interface_name: str) -> List[str]:
    """
    Get the private addresses assigned to a given network interface name and resource group pair.
    """
    ip_configs = network_client.network_interfaces.get(azure_resource_group, azure_interface_name)
    # ip_configs.ip_configurations = NetworkInterfaceIPConfiguration
    return [ip.private_ip_address for ip in ip_configs.ip_configurations]

def get_virtual_machine_details(network_client: NetworkManagementClient, vm) -> dict:
    """
    Resolve the virtual machine details, including interfaces and return a strucuted dict 
    
    The following attributes are keys in each dict with the key value type defined below:

        :param name: str # name of vm
        :param vm_id: str # unique UUID representing VM
        :param tags: dict[str, str] # tags assigned vm
        :param interface_ids: list[tuple(str, str)] # list of tuples for function args
        :param private_address: list[str] # ip addresses assigned private

    Azure VirtualMachine REST API does not expose a cleaner interface to obtaining
    network interface references so we're fetching the VMs in a given subscription/resource
    group and cross querying the network client API to get interface details and stitch
    that together here.
        
        https://github.com/Azure/azure-sdk-for-python/issues/534
    """
    vm_d = {
        'name': vm.name,
        'vm_id': vm.vm_id,
        'tags': vm.tags if vm.tags else {},
        'interface_ids': [],
        'private_address': []
    }
    # This will be a reference to the actual interface ID which will be in format:
    # /subscriptions/YOUR_SUBSCRIPTION_ID/resourceGroups/Hosts_Resources/providers/Microsoft.Network/networkInterfaces/windows152_z1
    # This is dissected to get the resource group and the interface name which will
    # be required by the network client to retrieve the interface details directly
    # Field #4 above is (Hosts_Resources) is the group name; groups cannot contain spaces
    # NOTE: This reduces the need to use a resource client to get resource groups

    for interface in vm.network_profile.network_interfaces:
        _interface = interface.id.split('/')
        if_name, r_group = _interface[-1], _interface[4]
        vm_d['private_address'].extend(get_private_address(network_client, r_group, if_name))
        vm_d['interface_ids'].append((if_name,r_group))
    return vm_d
    
def init_logging() -> None:
    """ Initialize logging """
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] - %(name)s %(message)s')
    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.ERROR)

def add_iplist(name, members):
	pass


if __name__ == '__main__':
    
    init_logging()
    load_dotenv() # take environment variables from .env

    parser = argparse.ArgumentParser(description='Virtual Machine Tag Collector')
    parser.add_argument('--debug', action='store_true', help='Enable verbose logging')
    parser.add_argument('--subscription', type=str, default=None, help='Filter by specific subscription id')
    parser.add_argument('--resource-group', nargs='?', default=[], help='Filter by specific resource group')
    parser.add_argument('--report_only', action='store_true', help='Do not create IPLists, just print azure data collected')
    
    config = parser.parse_args()
    if config.debug:
        logger.setLevel(logging.DEBUG)

    subscriptions = [config.subscription] if config.subscription else []

    # If subscription is set by environmental variable, overwrite by command line
    credential = EnvironmentCredential()

    # If a subscription was not specified, find the subscriptions allowed by this API client
    if not subscriptions:
        subscription_client = get_subscription_client(credential)
        for subscr in subscription_client.subscriptions.list():
            logger.info(f"Subscription: {subscr.id} id: {subscr.subscription_id} Tenant: {subscr.tenant_id}")
            subscriptions.append(subscr.subscription_id)

    if not subscriptions:
        logger.error(f"No subscriptions were found for client id: {os.getenv('AZURE_CLIENT_ID')} and tenant ID: {os.getenv('AZURE_TENANT_ID')}")
        sys.exit(1)

    logger.info(f"The following subscriptions will be scanned: {subscriptions}")
    
    result = {}

    for subscription_id in subscriptions:
        logger.info(f"Subscription id virtual machine check {subscription_id}")
        
        virtual_machines = [] # List of dict for each vm

        compute_client = get_compute_client(credential, subscription_id)
        network_client = get_network_management_client(credential, subscription_id)

        for vm in compute_client.virtual_machines.list_all():
            vm_d = get_virtual_machine_details(network_client, vm)
            virtual_machines.append(vm_d)
        
        result[subscription_id] = virtual_machines

    if config.report_only:
        pprint(result)
        sys.exit(0)

    # Establish connection to SMC
    session.login()

    iplists = {}	# Keep track of iplists, keys are list names and values is a list of IP addresses

    for subscription, values in result.items():
        print(f"Operating on subscription: {subscription}")
        for value in values:
            tags = value.get('tags')
            if tags:
                for tag, _value in tags.items():
                    name = f"{tag}_{_value}" if _value else f"{tag}"
                    iplists.setdefault(name, []).extend(value.get('private_address'))
        
    for listname, ipaddrs in iplists.items():
        # Update or create should only fire a pending change IF a new element is added or removed
	# The call to IPList sets append_lists=False which means whatever list of IPs that are sent in to SMC
	# will be used to populate the IPList (overwrite existing). 
	# This allows "deletions" to be processed successfully
	# Pending changes in SMC should still only fire when the IP list differs

        thelist = IPList.update_or_create(name=listname, iplist=ipaddrs, append_lists=False)
        print(f"Operated on iplist {thelist}")

    sys.exit(0)

"""
{'xxxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxxx': [{'interface_ids': [('machine37_z1', 'Hosts_Resources')],
                                            'name': 'machine',
                                            'private_address': ['10.0.0.4'],
                                            'tags': {},
                                            'vm_id': '780d7c49-f8ac-4bd0-bd19-36b44005f97c'},
                                            {'interface_ids': [('windows152_z1', 'Hosts_Resources')],
                                            'name': 'windows',
                                            'private_address': ['10.1.0.4'],
                                            'tags': {'some_host_type': '',
                                                    'some_other_tag_with_value': 'value_for_named_tag'},
                                            'vm_id': '686b60a0-a087-4bb5-9d45-ce3ec17f5da1'}]}
"""
