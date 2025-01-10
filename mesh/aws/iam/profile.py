"""a container for IAM roles attached to EC2 instances"""

import os
import pulumi_aws_native as aws_


def default():
    """default profile set in ~/.sky/config.yaml for SkyPilot VMs"""
    account_id = os.environ["AWS_ACCOUNT"]
    sky_ref = os.environ["LMRUN_SKY_REF"]

    role = aws_.iam.Role(
        sky_ref,
        role_name=sky_ref,
        assume_role_policy_document={
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
        },
        policies=[
            aws_.iam.RolePolicyArgs(
                policy_document={
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Action": "ec2:RunInstances",
                            "Resource": [
                                "arn:aws:ec2:*::image/ami-*",
                                f"arn:aws:ec2:*:{account_id}:instance/*",
                                f"arn:aws:ec2:*:{account_id}:network-interface/*",
                                f"arn:aws:ec2:*:{account_id}:subnet/*",
                                f"arn:aws:ec2:*:{account_id}:volume/*",
                                f"arn:aws:ec2:*:{account_id}:security-group/*",
                            ],
                        },
                        {
                            "Effect": "Allow",
                            "Action": [
                                "ec2:TerminateInstances",
                                "ec2:DeleteTags",
                                "ec2:StartInstances",
                                "ec2:CreateTags",
                                "ec2:StopInstances",
                            ],
                            "Resource": f"arn:aws:ec2:*:{account_id}:instance/*",
                        },
                        {
                            "Effect": "Allow",
                            "Action": ["ec2:Describe*"],
                            "Resource": "*",
                        },
                        {
                            "Effect": "Allow",
                            "Action": ["iam:GetRole", "iam:PassRole"],
                            "Resource": [f"arn:aws:iam::{account_id}:role/" + sky_ref],
                        },
                        {
                            "Effect": "Allow",
                            "Action": ["iam:GetInstanceProfile"],
                            "Resource": f"arn:aws:iam::{account_id}:instance-profile/{sky_ref}",
                        },
                        {
                            "Effect": "Allow",
                            "Action": "iam:CreateServiceLinkedRole",
                            "Resource": "*",
                            "Condition": {
                                "StringEquals": {
                                    "iam:AWSServiceName": "spot.amazonaws.com"
                                }
                            },
                        },
                    ],
                },
                policy_name=sky_ref + "SkyPilot",
            )
        ],
    )

    aws_.iam.InstanceProfile(
        sky_ref,
        instance_profile_name=sky_ref,
        # reference role_name from role to establish dependency
        roles=[role.role_name],
    )
