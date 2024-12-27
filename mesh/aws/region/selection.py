"""selection of regions covered by the network of VPCs"""

import pulumi

from aws.region.availability import availability

ROGUE_REGIONS = [
    # recent region in Malaysia isn't production-ready mid-December 2024
    # -> AWS::EC2::VPCGatewayAttachment is not yet supported via Cloud Control API
    "ap-southeast-5"
]


def vm_regions(main_region: str) -> list[str]:
    """return unique regions where at least one VM type is available"""
    vm_aws = pulumi.Config().require_object("vmAws")
    # list regions per instance type in a dict
    regions = availability(vm_aws)

    # add the main region: its VPC is required regardless of selected VMs
    deduped_regions = list(set(sum(regions.values(), [main_region])))

    print(
        "REMINDER review rogue regions to be excluded in aws.region.selection:",
        ROGUE_REGIONS,
    )
    # remove regions that are not production-ready, yet
    for rogue_region in ROGUE_REGIONS:
        if rogue_region in deduped_regions:
            deduped_regions.remove(rogue_region)

    return deduped_regions
