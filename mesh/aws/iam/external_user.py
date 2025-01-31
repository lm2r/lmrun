"""static credentials mounted on instances outside AWS"""

import json
import os
import pulumi_aws as aws_classic  # AccessKey not available in aws_native
from pulumi import Output
from aws.iam.policy.default import ext_vm_document


def write_credentials(key_id: str, secret: str):
    """create ~/.aws/ext-vm-credentials to later mount the file on external VMs"""
    file_name = "ext-vm-credentials"
    credentials = (
        f"[default]\naws_access_key_id={key_id}\naws_secret_access_key={secret}\n"
    )
    aws_dir = os.path.expanduser("~/.aws")
    os.makedirs(aws_dir, exist_ok=True)
    with open(os.path.join(aws_dir, file_name), "w", encoding="utf-8") as file:
        file.write(credentials)


def create_external_credentials_locally(main_region: str):
    """create local credentials, incl. IAM resources, granted to external VMs"""
    # create a user rather than a role to bound external credentials
    ext_vm = aws_classic.iam.User("external", name="external-vm", path="/lmrun/")
    access_key = aws_classic.iam.AccessKey(
        # increment suffix to rotate
        "external-0",
        user=ext_vm.name,
        # Active (default) or Inactive
        status="Active",
    )
    policy = aws_classic.iam.Policy(
        "external_vm",
        name="external-vm",
        description="limited LMRun privileges granted to external VMs outside AWS",
        policy=json.dumps(ext_vm_document(os.environ["AWS_ACCOUNT"], main_region)),
    )
    aws_classic.iam.UserPolicyAttachment(
        "external_user", user=ext_vm.name, policy_arn=policy.arn
    )
    Output.all(access_key.id, access_key.secret).apply(lambda x: write_credentials(*x))
