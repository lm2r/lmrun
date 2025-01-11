"""VPC peering"""

import ipaddress
import pulumi_aws_native as aws_


def peer(main_alloc: dict, alloc: dict, tag: aws_.TagArgs):
    """connect and route the main VPC with a satellite VPC"""
    # peer with main VPC
    pcx = aws_.ec2.VpcPeeringConnection(
        alloc["region"],
        peer_vpc_id=main_alloc["vpc"].vpc_id,
        vpc_id=alloc["vpc"].vpc_id,
        peer_region=main_alloc["region"],
        tags=[tag],
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


def main_private_interfaces(subnets: list[aws_.ec2.Subnet]):
    """private network interfaces to connect satellite VMs to fixed IPs in main VPC

    AWS reserves 5 IP addresses in each subnet for internal networking purposes:
    1. First IP address (.0) - Network address
    2. Second IP address (.1) - Reserved by AWS for the VPC router
    3. Third IP address (.2) - Reserved by AWS for DNS
    4. Fourth IP address (.3) - Reserved by AWS for future use
    5. Last IP address (.255 for /24) - Network broadcast address

    For example, in a subnet with CIDR block 10.0.0.0/24:
    - 10.0.0.0: Network address
    - 10.0.0.1: VPC router
    - 10.0.0.2: DNS server
    - 10.0.0.3: Reserved for future use
    - 10.0.0.4: -> LMRun private interface
    - 10.0.0.255: Broadcast address
    """
    for i, subnet in enumerate(subnets):
        aws_.ec2.NetworkInterface(
            "main_private" + str(i),
            subnet_id=subnet.subnet_id,
            private_ip_address=subnet.cidr_block.apply(
                lambda cidr: str(ipaddress.ip_network(cidr)[4])
            ),
            # AZ (not AZ ID) matches SKYPILOT_CLUSTER_INFO value
            tags=[aws_.TagArgs(key="Name", value=subnet.availability_zone)],
        )
