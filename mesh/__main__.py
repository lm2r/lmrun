"""Cluster Mesh, incl. security boundaries (IAM, SGs)"""

import os

from aws.region.selection import vm_regions
from aws.network import vpc
from aws.iam import profiles


main_region = os.environ["AWS_DEFAULT_REGION"]

# IAM Profiles: permission containers for instance roles
profiles.all_(main_region)

regions = vm_regions(main_region)
# cluster of networks peering all regions with the main
vpc.cluster(main_region, regions)
