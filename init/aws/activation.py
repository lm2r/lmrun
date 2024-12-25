"""activation of cloud regions"""

import boto3
import pulumi_aws as aws_classic


def enable_all_regions():
    """activate all regions where opt-in is required"""
    ec2 = boto3.client("ec2")
    all_regions = [
        (r["RegionName"], r["OptInStatus"])
        for r in ec2.describe_regions(AllRegions=True)["Regions"]
    ]
    for region, status in all_regions:
        if status != "opt-in-not-required":
            aws_classic.account.Region(
                region + "_opt-in", region_name=region, enabled=True
            )
