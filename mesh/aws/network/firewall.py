"""definitions of open ports"""

from pulumi import Output, ResourceOptions
from pulumi_aws_native.ec2 import (
    SecurityGroup,
    SecurityGroupIngress,
    SecurityGroupIngressArgs,
)
from constants import SKY_REF


def security_groups(region: str, vpc_id: Output, opts: ResourceOptions):
    """SG created in every region and referenced by name in ~/.sky/config.yaml"""
    sg = SecurityGroup(
        region + "_ssh",
        group_name=SKY_REF + "-ssh",
        group_description=f"default SSH port on {SKY_REF} instances",
        security_group_ingress=[
            SecurityGroupIngressArgs(
                ip_protocol="tcp", cidr_ip="0.0.0.0/0", from_port=22, to_port=22
            )
        ],
        vpc_id=vpc_id,
        opts=opts,
    )
    # allow inter-cluster communication with self-referencing ingress
    SecurityGroupIngress(
        region + "_self",
        ip_protocol="-1",  # all protocols
        group_id=sg.group_id,
        source_security_group_id=sg.group_id,
        opts=opts,
    )
