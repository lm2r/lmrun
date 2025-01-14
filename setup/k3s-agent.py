#!/usr/bin/env python3
"""K3s agent bootstrap"""

import os
import json
from socket import gethostbyname, gethostname
import subprocess
import requests


def run(command: list[str] | str, shell=False):
    """run a shell command from a list of strings, unless shell=True:
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


def get_parameter(suffix: str):
    """get server parameters to connect K3s agents"""
    name = f"/lmrun/{suffix}"
    print(f"get {name} from parameter store..")
    # no region_name, relying on AWS_DEFAULT_REGION where the server is located
    return boto3.client("ssm").get_parameter(
        Name=name,
        # ignored for String and StringList parameter types
        WithDecryption=True,
    )["Parameter"]["Value"]


def connection_options(cloud: str, agent_label: str) -> list[str]:
    """set K3s command flags to configure one of the two cases below

    ## 1. private connectivity (on AWS)
    k3s agent \
    --node-external-ip=<AGENT_EXTERNAL_IP> \
    --node-ip=<AGENT_INTERNAL_IP> \
    --server https://<SERVER_INTERNAL_IP>:6443

    ## 2. public connectivity (not on AWS)
    k3s agent \
    --node-external-ip=<AGENT_EXTERNAL_IP> \
    --node-ip=<AGENT_EXTERNAL_IP> \
    --server https://<SERVER_EXTERNAL_IP>:6443
    """
    K3S_SERVER_NAME = "main"

    def server_opt(ip: str):
        return f"--server=https://{ip}:6443"

    k3s_token = get_parameter(K3S_SERVER_NAME + "/token")
    agent_public_ip = requests.get(
        "https://checkip.amazonaws.com", timeout=2
    ).text.strip()
    opts = [
        "--token=" + k3s_token,
        "--node-external-ip=" + agent_public_ip,
        "--node-label=" + agent_label,
    ]

    if cloud.lower() == "aws":
        server_private_ip = get_parameter(K3S_SERVER_NAME + "/ip/private")
        agent_private_ip = gethostbyname(gethostname())
        opts += [
            server_opt(server_private_ip),
            "--node-ip=" + agent_private_ip,
        ]
    else:
        server_public_ip = get_parameter(K3S_SERVER_NAME + "/ip/public")
        opts += [
            server_opt(server_public_ip),
            "--node-ip=" + agent_public_ip,
        ]

    return opts


def node_label(name: str):
    """set a unique label to proxy service traffic targeting the VM"""
    # SKYPILOT_NUM_NODES isn't set on single-node clusters
    if os.environ.get("SKYPILOT_NUM_NODES", "1") == "1":
        return name
    return name + "-" + os.environ["SKYPILOT_SETUP_NODE_RANK"]


if __name__ == "__main__":
    cluster_info = json.loads(os.environ["SKYPILOT_CLUSTER_INFO"])
    cluster_name, cloud_name = cluster_info["cluster_name"], cluster_info["cloud"]

    k3s_command = ["curl", "-sfL", "https://get.k3s.io", "|", "sh", "-s", "-", "agent"]
    k3s_command += connection_options(cloud_name, node_label(cluster_name))
    run(" ".join(k3s_command), shell=True)
