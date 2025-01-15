#!/usr/bin/env python3
"""K3s server bootstrap"""

import os
import json
from typing import Literal
import secrets
import string
from socket import gethostbyname, gethostname
import subprocess
import requests


def run(command: list[str], shell=False):
    """Run a shell command from a list of strings, unless shell=True:
    i.e. command is a string and special characters are interpreted in a shell"""
    try:
        output = subprocess.run(
            command, shell=shell, check=True, capture_output=True, text=True
        )
        print("STDOUT:", output.stdout)
    except subprocess.CalledProcessError as e:
        print("STDERR:", e.stderr)
        raise e


run(["apt-get", "update"])
run(["apt-get", "install", "-y", "python3-boto3"])
import boto3  # pylint: disable=wrong-import-position


def generate_k3s_token(length=48):
    """Generate a secure random token for K3s"""
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def store_parameter(
    suffix: str,
    value: str,
    param_type: Literal["String", "SecureString"],
    region_name: str,
):
    """Store parameter to expose to K3s agents"""
    name = f"/lmrun/{suffix}"
    print(f"put {name} in parameter store..")
    boto3.client("ssm", region_name=region_name).put_parameter(
        Name=name,
        Value=value,
        Type=param_type,
        Overwrite=True,
    )


def instance_metadata(slug: str = "public-ipv4"):
    """Return instance metadata with authorized IMDSv2 scheme"""
    URL = "http://169.254.169.254/latest/"

    # get a token, TTL must be specified (max 21600)
    token_headers = {"X-aws-ec2-metadata-token-ttl-seconds": "60"}
    token = requests.put(URL + "api/token", headers=token_headers, timeout=2).text

    # use the token to get metadata
    metadata_url = URL + "meta-data/" + slug
    metadata_headers = {"X-aws-ec2-metadata-token": token}
    return requests.get(metadata_url, headers=metadata_headers, timeout=2).text


def connection_options():
    """Set K3s command flags to connect agents"""
    opts = []

    k3s_token = generate_k3s_token()
    store_parameter(cluster_name + "/token", k3s_token, "SecureString", region)
    opts += ["--token=" + k3s_token]

    private_ip = gethostbyname(gethostname())
    store_parameter(cluster_name + "/ip/private", private_ip, "String", region)
    opts += ["--advertise-address=" + private_ip]

    public_ip = instance_metadata(slug="public-ipv4")
    store_parameter(cluster_name + "/ip/public", public_ip, "String", region)
    opts += ["--node-external-ip=" + public_ip]

    return opts


if __name__ == "__main__":
    cluster_info = json.loads(os.environ["SKYPILOT_CLUSTER_INFO"])
    cluster_name, region = cluster_info["cluster_name"], cluster_info["region"]

    k3s_command = [
        "curl",
        "-sfL",
        "https://get.k3s.io",
        "|",
        "sh",
        "-s",
        "-",
        "server",
        "--flannel-external-ip",
        "--flannel-backend=wireguard-native",
        "--write-kubeconfig-mode=644",
    ]

    k3s_command += connection_options()
    run(" ".join(k3s_command), shell=True)

    with open("/etc/rancher/k3s/k3s.yaml", "r", encoding="utf-8") as file:
        kubeconfig = file.read()
    store_parameter(cluster_name + "/kubeconfig", kubeconfig, "SecureString", region)
