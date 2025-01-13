#!/usr/bin/env python3
"""K3s agent bootstrap"""

import os
import json
from socket import gethostbyname, gethostname
import requests
import subprocess

subprocess.run(["apt-get", "install", "-y", "python3-boto3"], check=True)
import boto3


def get_parameter(suffix: str):
    """get server parameters to connect K3s agents"""
    name = f"/lmrun/{suffix}"
    print(f"get {name} from parameter store..")
    # no region_name, relying on AWS_DEFAULT_REGION where the server is located
    boto3.client("ssm").get_parameter(
        Name=name,
        # ignored for String and StringList parameter types
        WithDecryption=True,
    )


def configure_environment(cloud: str):
    """set K3s environment variables to configure one of the two cases below
    
    # 1. private connectivity (on AWS)
    k3s agent \
    --node-external-ip=<AGENT_EXTERNAL_IP> \
    --node-ip=<AGENT_INTERNAL_IP> \
    --server https://<SERVER_INTERNAL_IP>:6443
    
    # 2. public connectivity (not on AWS)
    k3s agent \
    --node-external-ip=<AGENT_EXTERNAL_IP> \
    --node-ip=<AGENT_EXTERNAL_IP> \
    --server https://<SERVER_EXTERNAL_IP>:6443
    """
    on_private_network = cloud.lower() == "aws"

    k3s_token = get_parameter(K3S_SERVER_NAME + "/token")
    agent_public_ip = requests.get(
        "https://checkip.amazonaws.com", timeout=2
    ).text.strip()
    exports = [
        "K3S_TOKEN=" + k3s_token,
        "K3S_NODE_EXTERNAL_IP=" + agent_public_ip,
    ]
    if on_private_network:
        server_private_ip = get_parameter(K3S_SERVER_NAME + "/ip/private")
        agent_private_ip = gethostbyname(gethostname())
        exports += [
            "K3S_URL=" + server_private_ip,
            "K3S_NODE_IP=" + agent_private_ip,
        ]
    else:
        server_public_ip = get_parameter(K3S_SERVER_NAME + "/ip/public")
        exports += [
            "K3S_URL=" + server_public_ip,
            "K3S_NODE_IP=" + agent_public_ip,  # same as external IP
        ]

    # set environment variables on local system
    print("adding variables to /etc/environment..")
    for export in exports:
        with open("/etc/environment", "a", encoding="utf-8") as env_file:
            env_file.write(export + "\n")


if __name__ == "__main__":
    K3S_SERVER_NAME = "main"
    cluster_info = json.loads(os.environ["SKYPILOT_CLUSTER_INFO"])
    cluster_name, cloud = cluster_info["cluster_name"], cluster_info["cloud"]

    configure_environment(cloud)
    # TODO run `curl -sfL https://get.k3s.io | sh -`
