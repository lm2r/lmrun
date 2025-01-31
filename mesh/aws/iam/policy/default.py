"""default policy documents for VM roles"""


def read_main_node_params(account_id: str, main_region: str):
    """policy statement to grant read-only access to cluster credentials"""
    return [
        {
            "Effect": "Allow",
            "Action": "ssm:GetParameter",
            "Resource": [
                f"arn:aws:ssm:{main_region}:{account_id}:parameter/lmrun/main*",
            ],
        },
    ]


def ext_vm_document(account_id: str, main_region: str):
    """limited IAM policy document for external VMs outside AWS"""
    return {
        "Version": "2012-10-17",
        "Statement": read_main_node_params(account_id, main_region),
    }


def skypilot_statements(account_id: str, sky_ref: str):
    """policy statements derived from SkyPilot documentation"""
    return [
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
            "Condition": {"StringEquals": {"iam:AWSServiceName": "spot.amazonaws.com"}},
        },
    ]


def document(account_id: str, sky_ref: str, main_region: str):
    """default IAM policy document"""
    return {
        "Version": "2012-10-17",
        "Statement": skypilot_statements(account_id, sky_ref)
        + read_main_node_params(account_id, main_region),
    }
