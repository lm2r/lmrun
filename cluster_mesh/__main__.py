"""Cluster Mesh, incl. security boundaries (IAM, SGs)"""

import pulumi

from aws.region.selection import vm_regions
from aws.network import vpc
from aws.iam import profile


main_region = pulumi.Config("aws-native").require("region")

# IAM Profile: permission container including the instance role
profile.default()

regions = vm_regions(main_region)
# cluster of networks peering all regions with the main
vpc.cluster(main_region, regions)
