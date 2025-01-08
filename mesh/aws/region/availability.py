"""availability lookup of instance types per region"""

from typing import List
from concurrent.futures import ThreadPoolExecutor, as_completed
import boto3
from botocore.exceptions import ClientError


def check_region(region: str, instance_types: List[str]) -> tuple:
    """
    Check instance type availability for a single region.

    Args:
        region: AWS region name to check
        instance_types: List of instance types to check

    Returns:
        Tuple of (region, list of available instance types)
    """
    ec2 = boto3.client("ec2", region_name=region)
    try:
        response = ec2.describe_instance_type_offerings(
            LocationType="region",
            Filters=[{"Name": "instance-type", "Values": instance_types}],
        )
    except ClientError as e:
        message = (
            f"Boto3 client failed in {region}: is it a new region to activate? "
            "You may need to apply the cloud initialization stack in lmrun/init."
        )
        raise ValueError(message) from e

    available_types = [
        offering["InstanceType"] for offering in response["InstanceTypeOfferings"]
    ]
    return region, available_types


def availability(instance_types: List[dict[str, list[str]]]) -> dict:
    """
    Find all AWS regions that offer at least one of the specified instance types.

    Args:
        instance_types: List of AWS EC2 instance type strings to check

    Returns:
        Dictionary with instance types as keys and lists of available regions as values

    >>> from pprint import pprint
    >>> pprint(availability(["g6.xlarge", "inf2.xlarge"]))
    {'g6.xlarge': ['ap-northeast-1',
                   'ap-northeast-2',
                   'ap-south-1',
                   'ap-southeast-2',
                   'ap-southeast-5',
                   'ca-central-1',
                   'eu-central-1',
                   'eu-central-2',
                   'eu-north-1',
                   'eu-south-2',
                   'eu-west-2',
                   'eu-west-3',
                   'sa-east-1',
                   'us-east-1',
                   'us-east-2',
                   'us-west-2'],
     'inf2.xlarge': ['ap-northeast-1',
                     'ap-south-1',
                     'ap-southeast-1',
                     'ap-southeast-2',
                     'eu-central-1',
                     'eu-north-1',
                     'eu-west-1',
                     'eu-west-2',
                     'eu-west-3',
                     'sa-east-1',
                     'us-east-1',
                     'us-east-2',
                     'us-west-2']}
    """
    # Create EC2 client for region listing
    ec2 = boto3.client("ec2")

    # Get all regions
    regions = [
        region["RegionName"]
        for region in ec2.describe_regions(AllRegions=True)["Regions"]
    ]

    # Initialize results dictionary
    results = {instance_type: [] for instance_type in instance_types}

    # Check regions concurrently using ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=len(regions)) as executor:
        future_to_region = {
            executor.submit(check_region, region, instance_types): region
            for region in regions
        }

        for future in as_completed(future_to_region):
            region, available_types = future.result()

            # Add region to results for each available instance type
            for instance_type in available_types:
                if instance_type in results:
                    results[instance_type].append(region)

    # Sort the regions in each list
    for instance_type in results:
        results[instance_type].sort()

    return results


if __name__ == "__main__":
    import doctest

    doctest.testmod()
