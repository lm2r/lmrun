"""more permissive IAM policy document for the main cluster node"""


def document(account_id: str, main_region: str):
    """allow the main cluster node to edit cluster credentials"""
    return {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": "ssm:PutParameter",
                "Resource": [
                    f"arn:aws:ssm:{main_region}:{account_id}:parameter/lmrun/*",
                ],
            },
        ],
    }
