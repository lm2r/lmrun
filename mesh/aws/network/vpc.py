"""VPCs, incl. a main network peering with all others, subnets & routes"""

import os
from pulumi import ResourceOptions
import pulumi_aws_native as aws_

from aws.network.cidr_blocks import allocations
from aws.region.zones import enabled_az_ids
from aws.network.firewall import main_vm_sg, agent_vm_sg
from aws.network.peering import peer, main_private_interfaces


def cluster(main_region: str, regions: list[str]):
    """cluster of global and private networks routed to a central region"""
    selected_allocations = [a for a in allocations if a["region"] in regions]
    assert len(selected_allocations) == len(regions), (
        f"one of {regions} is missing a CIDR block allocation in cidr_blocks.py"
    )

    sky_ref = os.environ["LMRUN_SKY_REF"]
    ref_tag = aws_.TagArgs(key="Name", value=sky_ref)

    for alloc in selected_allocations:
        vpc_region = alloc["region"]
        region_provider = aws_.Provider(vpc_region, region=vpc_region)
        # pass these options to all new resources to target the right region
        alloc["opt"] = ResourceOptions(provider=region_provider)
        alloc["vpc"] = aws_.ec2.Vpc(
            vpc_region,
            cidr_block=alloc["cidr_block"],
            enable_dns_hostnames=True,
            enable_dns_support=True,
            tags=[ref_tag],
            opts=alloc["opt"],
        )
        alloc["ig"] = aws_.ec2.InternetGateway(
            vpc_region, tags=[ref_tag], opts=alloc["opt"]
        )
        aws_.ec2.VpcGatewayAttachment(
            vpc_region,
            vpc_id=alloc["vpc"].vpc_id,
            internet_gateway_id=alloc["ig"].internet_gateway_id,
            opts=alloc["opt"],
        )
        alloc["rt"] = aws_.ec2.RouteTable(
            vpc_region, vpc_id=alloc["vpc"].vpc_id, tags=[ref_tag], opts=alloc["opt"]
        )
        aws_.ec2.Route(
            vpc_region + "_public",
            route_table_id=alloc["rt"].route_table_id,
            gateway_id=alloc["ig"].internet_gateway_id,
            destination_cidr_block="0.0.0.0/0",
            opts=alloc["opt"],
        )

        # this paragraph creates VPC subnets
        #
        # ! use boto3 wrapper instead of aws_classic.get_availability_zones()
        # -> it doesn't call the region of the parent provider
        zones = enabled_az_ids(vpc_region)
        # split /16 IPv4 ranges into 8 x /19 blocks for up to 6 zones in region
        # -> arg. 13 are subnet bits, the inverse of subnet mask: 32 - 19
        alloc["subnet_blocks"] = aws_.cidr(
            ip_block=alloc["cidr_block"], count=len(zones), cidr_bits=13
        ).subnets
        alloc["subnets"] = []
        for i, zone_id in enumerate(zones):
            resource_name = vpc_region + str(i)
            alloc["subnets"].append(
                aws_.ec2.Subnet(
                    resource_name,
                    vpc_id=alloc["vpc"].vpc_id,
                    cidr_block=alloc["subnet_blocks"][i],
                    availability_zone_id=zone_id,
                    tags=[ref_tag],
                    opts=alloc["opt"],
                )
            )
            aws_.ec2.SubnetRouteTableAssociation(
                resource_name,
                route_table_id=alloc["rt"].route_table_id,
                subnet_id=alloc["subnets"][-1].subnet_id,
                opts=alloc["opt"],
            )

        # reassign main allocation to peer below after a full first loop
        if vpc_region == main_region:
            main_alloc = alloc

    # second loop to peer VPCs
    for alloc in selected_allocations:
        agent_vm_sg(
            alloc["region"],
            # same in main region, still allow traffic not covered by SG self-reference
            main_alloc["cidr_block"],
            alloc["vpc"].vpc_id,
            alloc["opt"],
        )
        if alloc["region"] != main_region:
            peer(main_alloc, alloc, ref_tag)
        else:
            main_vm_sg(
                main_region,
                selected_allocations,
                alloc["vpc"].vpc_id,
                alloc["opt"],
            )
            # private network interfaces to connect independent VMs to fixed IPs
            main_private_interfaces(main_alloc["subnets"])
