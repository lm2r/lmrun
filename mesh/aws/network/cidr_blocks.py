"""
Among the 3 RFC 1918 private IP ranges, only 10.0.0.0/8 can accommodate at least 50 /16 blocks.
- 50 is the default limit of active peered connections in a VPC
- /16 is the largest allocation possible
We don't combine ranges for simplicity.

Each region has been assigned a unique /16 CIDR block in the 10.0.0.0/8 range,
starting from 10.1.0.0/16 (skipping 10.0.0.0/16) due to AWS restrictions.
For more details, see https://docs.aws.amazon.com/vpc/latest/userguide/vpc-cidr-blocks.html
    -> #add-cidr-block-restrictions section in particular

! For clean updates, do not reallocate these ranges to new regions but add new ones at the bottom.

The list of all regions has been retrieved with:
```
boto3.client("ec2").describe_regions(AllRegions=True)["Regions"]
```
"""

import os
from typing import TypedDict


class Allocation(TypedDict):
    """data structure mapping each region to a network"""

    region: str
    cidr_block: str


main_region = os.environ["AWS_DEFAULT_REGION"]

# results in a memorable main IP ending in 4.0.4 after 4.0.0-3 reserved by AWS
main_allocation: Allocation = {"region": main_region, "cidr_block": "10.4.0.0/16"}
# removed 10.4.0.0 reserved for main allocation
default_allocations: list[Allocation] = [
    {"region": "af-south-1", "cidr_block": "10.1.0.0/16"},
    {"region": "ap-east-1", "cidr_block": "10.2.0.0/16"},
    {"region": "ap-northeast-1", "cidr_block": "10.3.0.0/16"},
    {"region": "ap-northeast-2", "cidr_block": "10.5.0.0/16"},
    {"region": "ap-northeast-3", "cidr_block": "10.6.0.0/16"},
    {"region": "ap-south-1", "cidr_block": "10.7.0.0/16"},
    {"region": "ap-south-2", "cidr_block": "10.8.0.0/16"},
    {"region": "ap-southeast-1", "cidr_block": "10.9.0.0/16"},
    {"region": "ap-southeast-2", "cidr_block": "10.10.0.0/16"},
    {"region": "ap-southeast-3", "cidr_block": "10.11.0.0/16"},
    {"region": "ap-southeast-4", "cidr_block": "10.12.0.0/16"},
    {"region": "ap-southeast-5", "cidr_block": "10.13.0.0/16"},
    {"region": "ca-central-1", "cidr_block": "10.14.0.0/16"},
    {"region": "ca-west-1", "cidr_block": "10.15.0.0/16"},
    {"region": "eu-central-1", "cidr_block": "10.16.0.0/16"},
    {"region": "eu-central-2", "cidr_block": "10.17.0.0/16"},
    {"region": "eu-north-1", "cidr_block": "10.18.0.0/16"},
    {"region": "eu-south-1", "cidr_block": "10.19.0.0/16"},
    {"region": "eu-south-2", "cidr_block": "10.20.0.0/16"},
    {"region": "eu-west-1", "cidr_block": "10.21.0.0/16"},
    {"region": "eu-west-2", "cidr_block": "10.22.0.0/16"},
    {"region": "eu-west-3", "cidr_block": "10.23.0.0/16"},
    {"region": "il-central-1", "cidr_block": "10.24.0.0/16"},
    {"region": "me-central-1", "cidr_block": "10.25.0.0/16"},
    {"region": "me-south-1", "cidr_block": "10.26.0.0/16"},
    {"region": "sa-east-1", "cidr_block": "10.27.0.0/16"},
    {"region": "us-east-1", "cidr_block": "10.28.0.0/16"},
    {"region": "us-east-2", "cidr_block": "10.29.0.0/16"},
    {"region": "us-west-1", "cidr_block": "10.30.0.0/16"},
    {"region": "us-west-2", "cidr_block": "10.31.0.0/16"},
    # exclude k3s --cluster-cidr default "10.42.0.0/16"	reserved for pod IPs
]
allocations = [
    alloc if alloc["region"] != main_region else main_allocation
    for alloc in default_allocations
]
