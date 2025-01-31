"""definitions of open ports"""

import os
from pulumi import Output, ResourceOptions
from pulumi_aws_native.ec2 import (
    SecurityGroup,
    SecurityGroupIngress,
    SecurityGroupIngressArgs,
    PrefixList,
    PrefixListEntryArgs,
)

from aws.network.cidr_blocks import Allocation

SSH_INGRESS = SecurityGroupIngressArgs(
    ip_protocol="tcp", cidr_ip="0.0.0.0/0", from_port=22, to_port=22
)
VPN_INGRESS = SecurityGroupIngressArgs(
    ip_protocol="udp", cidr_ip="0.0.0.0/0", from_port=51820, to_port=51820
)
# reference the same name in all VM security groups for global SkyPilot config
sky_ref = os.environ["LMRUN_SKY_REF"]


def self_referencing_ingress(region: str, sg_id: Output, opts: ResourceOptions):
    """allow VPC traffic for regional clusters with self-referencing ingress"""
    SecurityGroupIngress(
        region + "_self",
        ip_protocol="-1",  # all protocols
        group_id=sg_id,
        source_security_group_id=sg_id,
        opts=opts,
    )


def main_vm_sg(
    region: str, allocations: list[Allocation], vpc_id: Output, opts: ResourceOptions
):
    """SG in main region and referenced by name in ~/.sky/config.yaml"""
    pl = PrefixList(
        "satellite_blocks",
        address_family="IPv4",
        entries=[
            PrefixListEntryArgs(cidr=alloc["cidr_block"], description=alloc["region"])
            for alloc in allocations
        ],
        # this property is required when creating a prefix list
        max_entries=55,  # max max_entries 60 minus other ingress like SSH or VPN
        prefix_list_name="SatelliteBlocks",
        opts=opts,
    )
    sg = SecurityGroup(
        region,
        group_name=sky_ref,
        group_description=f"SSH and satellite VPC inbound on {sky_ref} instances",
        security_group_ingress=[
            SSH_INGRESS,
            VPN_INGRESS,
            SecurityGroupIngressArgs(
                ip_protocol="-1", source_prefix_list_id=pl.prefix_list_id
            ),
            # K3s agents need access to 6443 on the server for:
            # - initial registration, secured by K3s token
            # - getting cluster CA certificates
            # - Kubernetes API server communication, secured by kubeconfig certificate
            SecurityGroupIngressArgs(
                ip_protocol="tcp", cidr_ip="0.0.0.0/0", from_port=6443, to_port=6443
            ),
        ],
        vpc_id=vpc_id,
        opts=opts,
    )
    self_referencing_ingress(region, sg.group_id, opts)


def satellite_vm_sg(
    region: str, main_region_cidr: str, vpc_id: Output, opts: ResourceOptions
):
    """SG in satellite regions and referenced by name in ~/.sky/config.yaml"""
    sg = SecurityGroup(
        region,
        group_name=sky_ref,
        group_description=f"SSH and main VPC inbound on {sky_ref} instances",
        security_group_ingress=[
            SSH_INGRESS,
            VPN_INGRESS,
            SecurityGroupIngressArgs(ip_protocol="-1", cidr_ip=main_region_cidr),
        ],
        vpc_id=vpc_id,
        opts=opts,
    )
    self_referencing_ingress(region, sg.group_id, opts)
