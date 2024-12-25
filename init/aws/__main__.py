"""bootstrap cloud resources to track Pulumi states in remote backends"""

import pulumi_aws_native as aws

from activation import enable_all_regions


enable_all_regions()

# retrieve account id to create unique bucket names
account = aws.get_account_id_output()

# pass `state` as a lambda argument, DO NOT add directly to string, otherwise:
# the last state overrides the first when `apply` is called async after the loop
for state in ["admin", "app"]:
    aws.s3.Bucket(
        state + "_state",
        bucket_name=account.apply(lambda a, s=state: f"pulumi-{s}-{a.account_id}"),
    )

    key_resource_name = state + "_state_key"
    # do not specify a key policy: the default enables IAM policies
    key = aws.kms.Key(
        key_resource_name,
        description=f"Pulumi {state} state",
        enabled=True,
        # Pulumi standard, see https://github.com/pulumi/pulumi/issues/17649
        key_spec="SYMMETRIC_DEFAULT",
    )
    aws.kms.Alias(
        key_resource_name, target_key_id=key.key_id, alias_name="alias/pulumi/" + state
    )
