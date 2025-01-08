"""availability zones in AWS regions"""

import boto3


def enabled_az_ids(region_name: str) -> list[str]:
    """
    Return IDs of enabled zones for a single region.

    Args:
        region_name: AWS region name

    Returns:
        List of IDs

    >>> sorted(enabled_az_ids("us-east-1"))
    ['use1-az1', 'use1-az2', 'use1-az3', 'use1-az4', 'use1-az5', 'use1-az6']
    >>> sorted(enabled_az_ids("ap-northeast-1"))
    ['apne1-az1', 'apne1-az2', 'apne1-az4']
    """
    ec2_client = boto3.client("ec2", region_name=region_name)

    response = ec2_client.describe_availability_zones(
        Filters=[
            {"Name": "region-name", "Values": [region_name]},
            {"Name": "state", "Values": ["available"]},
        ]
    )

    azs = [(az["ZoneName"], az["ZoneId"]) for az in response["AvailabilityZones"]]
    # sort by AZ name for deterministic mapping with network interface IP,
    # e.g. by iterating in order, us-east-1a subnet will be 10.4.0.x,
    #                             us-east-1b                10.4.32.x, etc.
    return [id for _, id in sorted(azs, key=lambda x: x[0])]


if __name__ == "__main__":
    import doctest

    doctest.testmod()
