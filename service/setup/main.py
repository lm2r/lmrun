#!/usr/bin/env python3
"""setup of K3s main server"""

import os
import json
from typing import Literal
import secrets
import string
from socket import gethostbyname, gethostname
import requests
import boto3


def generate_k3s_token(length=48):
    """generate a secure random token for K3s"""
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def store_parameter(
    suffix: str,
    value: str,
    param_type: Literal["String", "SecureString"],
    region_name: str,
):
    """store parameter in store to expose to K3s agents"""
    name = f"/lmrun/{suffix}"
    print(f"put {name} in parameter store..")
    boto3.client("ssm", region_name=region_name).put_parameter(
        Name=name,
        Value=value,
        Type=param_type,
        Overwrite=True,
    )


def instance_metadata(slug: str = "public-ipv4"):
    """return instance metadata with authorized IMDSv2 scheme"""
    URL = "http://169.254.169.254/latest/"

    # get a token, max session length: 6 hours
    token_headers = {"X-aws-ec2-metadata-token-ttl-seconds": "21600"}
    token = requests.put(URL + "api/token", headers=token_headers, timeout=2).text

    # use the token to get metadata
    metadata_url = URL + "meta-data/" + slug
    metadata_headers = {"X-aws-ec2-metadata-token": token}
    return requests.get(metadata_url, headers=metadata_headers, timeout=2).text


if __name__ == "__main__":
    cluster_info = json.loads(os.environ["SKYPILOT_CLUSTER_INFO"])
    cluster_name, region = cluster_info["cluster_name"], cluster_info["region"]

    k3s_token = generate_k3s_token()
    store_parameter(cluster_name + "/token", k3s_token, "SecureString", region)

    private_ip = gethostbyname(gethostname())
    store_parameter(cluster_name + "/ip/private", private_ip, "String", region)

    public_ip = instance_metadata(slug="public-ipv4")
    store_parameter(cluster_name + "/ip/public", public_ip, "String", region)

    # set environment variables on local system
    exports = [
        "K3S_TOKEN=" + k3s_token,
        "INT_K3S_URL=" + private_ip,
        "EXT_K3S_URL=" + public_ip,
    ]
    print("adding variables to /etc/environment..")
    for export in exports:
        with open("/etc/environment", "a", encoding="utf-8") as env_file:
            env_file.write(export + "\n")
