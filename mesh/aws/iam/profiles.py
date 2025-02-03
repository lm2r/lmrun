"""containers for IAM roles attached to EC2 instances"""

import os
import pulumi_aws_native as aws_
from aws.iam import roles


def default(account_id: str, sky_ref: str, main_region: str):
    """default profile set in ~/.sky/config.yaml for SkyPilot VMs"""
    role = roles.default(account_id, sky_ref, main_region)
    aws_.iam.InstanceProfile(
        sky_ref,
        instance_profile_name=sky_ref,
        roles=[role.role_name],
    )


def main(account_id: str, sky_ref: str, main_region: str):
    """profile for main cluster nodes: starting with 'main*' in sky/config.yaml"""
    NAME = sky_ref + "-main"
    role = roles.main(account_id, sky_ref, NAME, main_region)
    aws_.iam.InstanceProfile(
        NAME,
        instance_profile_name=NAME,
        roles=[role.role_name],
    )


def all_(main_region: str):
    """call from __main__.py to deploy all EC2 profiles at once"""
    account_id = os.environ["AWS_ACCOUNT"]
    sky_ref = os.environ["LMRUN_SKY_REF"]
    default(account_id, sky_ref, main_region)
    main(account_id, sky_ref, main_region)
