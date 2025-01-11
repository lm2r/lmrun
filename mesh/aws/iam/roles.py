"""IAM roles for AWS VMs"""

from functools import cache
from pulumi_aws_native.iam import Role, RolePolicyArgs
from aws.iam.policy.default import document as default_policy_doc
from aws.iam.policy.main import document as main_policy_doc


TRUST_POLICY_DOC = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": [
                    "ec2.amazonaws.com",
                ],
            },
            "Action": "sts:AssumeRole",
        }
    ],
}


@cache
def default_policy(account_id: str, sky_ref: str, main_region: str):
    "shared default policy resource"
    return RolePolicyArgs(
        policy_document=default_policy_doc(account_id, sky_ref, main_region),
        policy_name=sky_ref + "Default",
    )


def default(account_id: str, sky_ref: str, main_region: str):
    """default VM role"""
    return Role(
        sky_ref,
        role_name=sky_ref,
        assume_role_policy_document=TRUST_POLICY_DOC,
        policies=[default_policy(account_id, sky_ref, main_region)],
    )


def main(account_id: str, sky_ref: str, name: str, main_region: str):
    """main VM role"""
    return Role(
        name,
        role_name=name,
        assume_role_policy_document=TRUST_POLICY_DOC,
        policies=[
            default_policy(account_id, sky_ref, main_region),
            RolePolicyArgs(
                policy_document=main_policy_doc(account_id, main_region),
                policy_name=sky_ref + name.capitalize(),
            ),
        ],
    )
