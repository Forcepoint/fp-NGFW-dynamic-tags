"""
Collect EC2 instance mappings from AWS

Authentication is done using normal boto3 methods documented here:

https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html

The configuration file location will first be attempted from the local directory where a file
named 'config' could be located alongside this script. If it doesn't exist, normal AWS methods
are attempted.

See the config.env example file which just mirrors (and in fact just points to) the config
file location in the current directory as a convenience. It can still be located whereever and
used the same way you normally use your ~.aws/credentials, etc mappings.

The only requirement is that the credentials used by this script has access to the following roles:

AmazonEC2ReadOnlyAccess
AmazonVPCReadOnlyAccess

"""
import os
import sys
import logging
import argparse
from pathlib import Path
from dotenv import load_dotenv
from pprint import pprint
from smc import session
from smc.elements.network import IPList

import boto3
from botocore.exceptions import ClientError


logger = logging.getLogger(__name__)

def describe_vpcs(ec2_client, name: str = None, next_token: str = None, max_items=100):
    """
    Get VPC info paginator
    """
    try:
        # creating paginator object for describe_vpcs() method
        paginator = ec2_client.get_paginator('describe_vpcs')

        if name:
            filters = [{
                'Name': 'tag:Name',
                'Values': [name]
            }]
        else:
            filters = [{
                'Name': 'tag:Name', 
                'Values': ['*']
            }]

        pagination_config = {'MaxItems': max_items}
        if next_token:
            pagination_config['StartingToken'] = next_token
        
        # creating a PageIterator from the paginator
        response_iterator = paginator.paginate(
            Filters=filters,
            PaginationConfig=pagination_config)

        full_result = response_iterator.build_full_result()
        logger.debug(full_result)

        vpc_list = []

        for page in full_result['Vpcs']:
            # Return an abbreviated version of the dict, override this possibly in kwargs
            vpc_name = None
            tags = page.get('Tags', [])
            for tag in tags:
                if tag.get('Key') == 'Name':
                    vpc_name = tag.get('Value')
                    break
            if not vpc_name:
                vpc_name = 'Unknown'
            
            new_page = {'name': vpc_name, 'vpc_id': page.get('VpcId')}
            vpc_list.append(new_page)
    
    except ClientError:
        logger.exception('Client error during VPC check')
        raise
    else:
        return vpc_list, full_result.get('NextToken', None)

def describe_vpc_all(ec2_client, page_size=100):
    """ Iterator yielding pages """
    first_result, next_token = describe_vpcs(ec2_client, max_items=page_size)
    yield first_result
    while next_token is not None:
        result, next_token = describe_vpcs(ec2_client, next_token=next_token, max_items=page_size)
        yield result

def describe_instances(ec2_client, name: str = None, next_token: str = None, ec2_states: list = None, max_items: int = 100):
    """
    Get EC2 instance paginator
    """
    try:
        paginator = ec2_client.get_paginator('describe_instances')

        if name:
            filters = [{
                'Name': 'tag:Name',
                'Values': [name]
            }]
        else:
            filters = [{
                'Name': 'tag:Name', 
                'Values': ['*']
            }]

        if ec2_states:
            filters.append({
                'Name': 'instance-state-name',
                'Values': ec2_states
            })
        
        pagination_config = {'MaxItems': max_items}
        if next_token:
            pagination_config['StartingToken'] = next_token
        
        # creating a PageIterator from the paginator
        response_iterator = paginator.paginate(
            Filters=filters,
            PaginationConfig=pagination_config)

        full_result = response_iterator.build_full_result()
        logger.debug(full_result)
        
        ec2_list = []

        # Tags in AWS are parsed and the 'Name' key field used as the instance name if it exists
        # That is then removed as we will not need an individual IPList per instance
        
        reservations = full_result.get('Reservations', [])
        for page in reservations:
            # Iterate the instances within the reservation
            for instance in page.get('Instances', []):
                instance_name = None
                tags = []
                for tag in instance.get('Tags', []):
                    if tag.get('Key') == 'Name':    # This is our name tag
                        instance_name = tag.get('Value')
                    else:                           # Custom tag that will be used for grouping
                        tags.append(tag)                 
                
                if not instance_name:
                    instance_name = 'Unknown'

                # Pickup the AZ also, may be interesting..
                placement = instance.get('Placement', {}).get('AvailabilityZone', 'unknown')

                address_list = []
                # Collect our PrivateIpAddresses from the network interface list
                for network_interface in instance.get('NetworkInterfaces', []):
                    private_ip_addresses = network_interface.get('PrivateIpAddresses', [])
                    for private_addr in private_ip_addresses:
                        address_list.append(private_addr.get('PrivateIpAddress'))
                
                new_page = {'name': instance_name, 'vpc_id': instance.get('VpcId'), 'tags': tags, 
                    'private_address': address_list, 'placement': placement}
                ec2_list.append(new_page)
    
    except ClientError:
        logger.exception('Client error during EC2 instance check')
        raise
    else:
        return ec2_list, full_result.get('NextToken', None)

def describe_instances_all(ec2_client, ec2_states: list = None, page_size=100):
    """ Iterator yielding pages """
    first_result, next_token = describe_instances(ec2_client, ec2_states=ec2_states, max_items=page_size)
    yield first_result
    while next_token is not None:
        result, next_token = describe_instances(ec2_client, next_token=next_token, ec2_states=ec2_states, max_items=page_size)
        yield result

def init_logging() -> None:
    """ Initialize logging """
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] - %(name)s %(message)s')
    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.ERROR)

def init_config() -> None:
    """ Initialize the AWS config from local dir, otherwise this will drop down to default AWS locations """
    local_cfg = Path(__file__).parent.absolute() / "config"
    if local_cfg.exists():
        os.environ['AWS_SHARED_CREDENTIALS_FILE'] = str(local_cfg)
        load_dotenv(dotenv_path=local_cfg)

def usage(name=None):
    if not name:
        name = os.path.basename(__file__)
    examples = f"""
    
    Override the client region when connecting:

    {name} --region us-west-1

    Run a report on the results returned from the query. By default, only AWS boto3 is called. No IPLists are created
    on the SMC:

    {name} --report_only

    Only return instance VMs that have a specific state of running:

    {name} --ec2_states running

    If an instance is untagged, you can specify a custom group for it, otherwise it is placed in untagged-<AZ>, where
    <AZ> is the availability zone for the VM:

    {name} --untagged_group 'lostandfound'

    For larger environments, set a page size (default 100) for paginators:

    {name} --page_size 100

    """
    return examples

if __name__ == '__main__':

    init_logging()
    init_config()

    parser = argparse.ArgumentParser(description='Virtual Machine Tag Collector', usage=usage())
    parser.add_argument('--debug', action='store_true', help='Enable verbose logging')
    parser.add_argument('--region', type=str, help='Optional region for VPCs')
    parser.add_argument('--page_size', type=int, default=100, help='Max results requested from remote SDK in pages. Used when iterating all.')
    parser.add_argument('--ec2_states', type=str, default=None, help='Comma seperated list specifying VM states to filter on - default no filter')
    parser.add_argument('--skip_vpc_discovery', action='store_true', default=False, help='Skip the VPC discovery process to obtain VPC names')
    parser.add_argument('--untagged_group', type=str, help='Some elements may be untagged, where do these get placed. By default, untagged_<region>')
    parser.add_argument('--tag_filters', type=str, default=None, help='Optionally filter instances on specific tags. By default, no filters')
    parser.add_argument('--report_only', action='store_true', help='Do not create IPLists, just print azure data collected')
    
    config = parser.parse_args()
    if config.debug:
        logger.setLevel(logging.DEBUG)

    # Get an EC2 client. Will fail here if credentials are not found
    # Region can be overidden from AWS methods if provided on command line
    if config.region:
        ec2_client = boto3.client('ec2', region_name=config.region)
    else:    
        ec2_client = boto3.client('ec2')

    # We can extract other attributes if we want to get VPC names for instance (which would be useful).
    vpc_ids = []

    if not config.skip_vpc_discovery:
        # These will come back in page size batches
        for vpc in describe_vpc_all(ec2_client, page_size=config.page_size):
            vpc_ids.append(vpc)

    # Optionally only obtain results for instances with specified states
    ec2_states = config.ec2_states.split(',') if config.ec2_states else []
    
    if config.report_only:
        print(f"VPCs: {vpc_ids}")
        for batch in describe_instances_all(ec2_client, ec2_states=ec2_states, page_size=config.page_size):
            pprint(batch)
        
    if not config.report_only:
        # Establish connection to SMC
        session.login()

    iplists = {}	# Keep track of iplists, keys are list names and values is a list of IP addresses

    for batch in describe_instances_all(ec2_client, ec2_states=ec2_states, page_size=config.page_size):
        for instance in batch:
            tags = instance.get('tags', [])
            if tags:
                for tag in tags:
                    key = tag.get('Key', '').replace(' ', '_')
                    value = tag.get('Value', '').replace(' ', '_')
                    name = f"{key}_{value}"
                    iplists.setdefault(name, []).extend(instance.get('private_address'))
            else:
                # Ungrouped. Put in ungrouped based on region unless overridden in command line
                if config.untagged_group:
                    name = f'{config.untagged_group}'
                else:
                    name = f'untagged-aws-{instance.get("placement")}'
                
                iplists.setdefault(name, []).extend(instance.get('private_address'))
    
    if config.report_only:
        pprint(iplists)
        sys.exit(0)
    
    # Make the modification to SMC

    for listname, ipaddrs in iplists.items():
        # Update or create should only fire a pending change IF a new element is added or removed
    	# The call to IPList sets append_lists=False which means whatever list of IPs that are sent in to SMC
	    # will be used to populate the IPList (overwrite existing). 
	    # This allows "deletions" to be processed successfully
	    # Pending changes in SMC should still only fire when the IP list differs

        thelist = IPList.update_or_create(name=listname, iplist=ipaddrs, append_lists=False)
        print(f"Operated on iplist {thelist}")

    sys.exit(0)