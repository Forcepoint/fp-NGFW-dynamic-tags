"""
GCP interface to Forcepoint NGFW for tag synchronization

https://cloud.google.com/python/docs/reference

python3 main.py --project_id fpngf-293813 --report_only

This looks for the GCP credentials in the local directory in a file named gcp.json

The `gcp.json` is the service credential authentication information required for this API client
to connect and should have been downloaded as part of the credential creation.

In addition, Forcepoint SMC credentials are required to bridge the connection to SMC.
By default, you can put SMC auth ENV vars in .env or you can configure ~.smcrc as you normally would
use FP smcpython.

"""
import os
import sys
import argparse
from pathlib import Path
from typing import Iterable, Dict
from pprint import pprint

import logging

from dotenv import load_dotenv
from google.cloud import compute_v1

from smc import session
from smc.elements.network import IPList

logger = logging.getLogger(__name__)

def list_instances(project_id: str, zone: str) -> Iterable[compute_v1.Instance]:
    """
    List all instances in the given zone in the specified project.

    Args:
        project_id: project ID or project number of the Cloud project you want to use.
        zone: name of the zone you want to use. For example: “us-west3-b”
    Returns:
        An iterable collection of Instance objects.
    """
    instance_client = compute_v1.InstancesClient()
    instance_list = instance_client.list(project=project_id, zone=zone)
    return instance_list

def list_all_instances(project_id: str, page_size: int = 100) -> Dict[str, Dict]:
    """
    Returns a dictionary of all instances present in a project, grouped by their zone.

    Args:
        project_id: project ID or project number of the Cloud project you want to use.
    Returns:
        A dictionary with zone names as keys (in form of "zones/{zone_name}") and
        iterable collections of Instance objects as values.
    """
    instance_client = compute_v1.InstancesClient()
    request = compute_v1.AggregatedListInstancesRequest()
    request.project = project_id
    # Use the `max_results` parameter to limit the number of results that the API returns per response page.
    request.max_results = page_size

    agg_list = instance_client.aggregated_list(request=request)

    all_instances = {}
    # Despite using the `max_results` parameter, you don't need to handle the pagination
    # yourself. The returned `AggregatedListPager` object handles pagination
    # automatically, returning separated pages as you iterate over the results.
    for zone, response in agg_list:
        if response.instances:
            all_instances.setdefault(zone, [])
            for instance in response.instances:
                hostdata = {'private_addresses': [], 'labels': instance.labels}
                
                for net in instance.network_interfaces:
                    hostdata.setdefault('private_address', []).append(net.network_i_p)
                all_instances.setdefault(zone, []).append(hostdata)
    return all_instances

def init_logging() -> None:
    """ Initialize logging """
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] - %(name)s %(message)s')
    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.ERROR)

def init_config() -> None:
    """ Initialize GCP and API creds """
    local_cfg = Path(__file__).parent.absolute() / "gcp.json"
    if local_cfg.exists():
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = str(local_cfg)
    
if __name__ == '__main__':
    
    init_logging()
    init_config()
    load_dotenv()

    parser = argparse.ArgumentParser(description='Virtual Machine Tag Collector')
    parser.add_argument('--debug', action='store_true', help='Enable verbose logging')
    parser.add_argument('--project_id', type=str, required=True, help='Filter by specific subscription id')
    parser.add_argument('--zone', default=None, type=str, help='Specify zone for project')
    parser.add_argument('--page_size', type=int, default=100, help='Max results requested from remote SDK in pages. Used when iterating all.')
    parser.add_argument('--report_only', action='store_true', help='Do not create IPLists, just print azure data collected')
    
    config = parser.parse_args()
    if config.debug:
        logger.setLevel(logging.DEBUG)

    if config.zone:
        instances = list_instances(project_id=config.project_id,zone=config.zone)
    else:
        instances = list_all_instances(project_id=config.project_id)
        
    if config.report_only:
        pprint(instances)
    
    if not config.report_only:
        # Establish connection to SMC
        session.login()

    iplists = {}	# Keep track of iplists, keys are list names and values is a list of IP addresses

    # Zones are all prefixed with zone/<NAME>
    for zone, instance in instances.items():
        
        for host in instance:
            for key, value in host.get('labels', {}).items():
                name = f"{key}_{value}" if value else  key
                iplists.setdefault(name, []).extend(host.get('private_address'))
    
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