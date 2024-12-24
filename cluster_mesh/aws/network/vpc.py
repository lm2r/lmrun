"""VPCs, incl. a main network peering with all others, subnets & routes"""

from pulumi import ResourceOptions
import pulumi_aws_native as aws_

from constants import SKY_REF
from aws.network.cidr_blocks import allocations
from aws.region.zones import enabled_az_ids
from aws.network.firewall import security_groups


def cluster(main_region: str, regions: list[str]):
    """cluster of global and private networks routed to a central region"""
    selected_allocations = [a for a in allocations if a["region"] in regions]
    assert len(selected_allocations) == len(
        regions
    ), f"one of {regions} is missing a CIDR block allocation in cidr_blocks.py"

    ref_tag = aws_.TagArgs(key="Name", value=SKY_REF)

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

        if vpc_region == main_region:
            main_alloc = alloc

    # second loop to peer VPCs and configure firewall (security groups)
    for alloc in selected_allocations:
        security_groups(alloc["region"], alloc["vpc"].vpc_id, alloc["opt"])

        if alloc["region"] != main_region:
            # peer with main VPC
            pcx = aws_.ec2.VpcPeeringConnection(
                alloc["region"],
                peer_vpc_id=main_alloc["vpc"].vpc_id,
                vpc_id=alloc["vpc"].vpc_id,
                peer_region=main_region,
                tags=[ref_tag],
                opts=alloc["opt"],
            )
            # route entire VPCs to each other
            aws_.ec2.Route(
                alloc["region"] + "_private_outbound",
                route_table_id=alloc["rt"].route_table_id,
                destination_cidr_block=main_alloc["cidr_block"],
                vpc_peering_connection_id=pcx.id,
                opts=alloc["opt"],
            )
            aws_.ec2.Route(
                alloc["region"] + "_private_inbound",
                route_table_id=main_alloc["rt"].route_table_id,
                destination_cidr_block=alloc["cidr_block"],
                vpc_peering_connection_id=pcx.id,
                opts=main_alloc["opt"],
            )
