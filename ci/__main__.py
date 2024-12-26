"""GitHub OIDC provider to let tests interact with the cloud environment in CI"""

import os
import pulumi_aws_native as aws_
import pulumi_github as github


URL = "token.actions.githubusercontent.com"
AUDIENCE = "sts.amazonaws.com"
ROLE_NAME = "LMRunCI"
REPO = "lmrun"
gh_account = os.environ["GITHUB_OWNER"]

# aws.amazon.com/blogs/security/use-iam-roles-to-connect-github-actions-to-actions-in-aws
oidc_provider = aws_.iam.OidcProvider(
    "github",
    client_id_list=[AUDIENCE],
    # a single provider is allowed per url in an AWS account
    url="https://" + URL,
    thumbprint_list=["6938fd4d98bab03faadb97b34396831e3780aea1"],
)

role = aws_.iam.Role(
    "ci",
    # authorizing any branch 'heads/*' for read-only permissions
    assume_role_policy_document={
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Federated": oidc_provider.arn,
                },
                "Action": "sts:AssumeRoleWithWebIdentity",
                "Condition": {
                    "StringLike": {
                        URL + ":sub": f"repo:{gh_account}/{REPO}:ref:refs/heads/*"
                    },
                    "StringEquals": {URL + ":aud": AUDIENCE},
                },
            }
        ],
    },
    role_name=ROLE_NAME,
    policies=[
        aws_.iam.RolePolicyArgs(
            policy_name=ROLE_NAME + "-RegionMetadata",
            policy_document={
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": [
                            "ec2:DescribeAvailabilityZones",
                            "ec2:DescribeRegions",
                            "ec2:DescribeInstanceTypeOfferings",
                        ],
                        "Resource": ["*"],
                    }
                ],
            },
        ),
    ],
)

github.ActionsSecret(
    "ci_aws_role", repository=REPO, secret_name="CI_AWS_ROLE", plaintext_value=role.arn
)
# required in aws-actions/configure-aws-credentials
github.ActionsVariable(
    "aws_default_region",
    repository=REPO,
    variable_name="AWS_DEFAULT_REGION",
    value=os.environ["AWS_DEFAULT_REGION"],
)
