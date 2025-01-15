#!/usr/bin/env python3
"""K3s agent bootstrap"""

import os
import json
from socket import gethostbyname, gethostname
import argparse
import requests
from k3s_agent_util import run, host_service


run(["apt-get", "update"])
run(["apt-get", "install", "-y", "python3-boto3"])
import boto3  # pylint: disable=wrong-import-position

K3S_SERVER_NAME = "main"


def read_port_arg():
    """Parse optional port argument"""
    parser = argparse.ArgumentParser()
    # nullish default value (0) to apply a service if set
    parser.add_argument("--port", type=int, default=0)
    args = parser.parse_args()
    return args.port


def get_parameter(suffix: str):
    """Get server parameters to connect K3s agents"""
    name = f"/lmrun/{suffix}"
    print(f"get {name} from parameter store..")
    # no region_name, relying on AWS_DEFAULT_REGION where the server is located
    return boto3.client("ssm").get_parameter(
        Name=name,
        # ignored for String and StringList parameter types
        WithDecryption=True,
    )["Parameter"]["Value"]


def connection_options(cloud: str, agent_label: str) -> list[str]:
    """Set K3s command flags to configure one of these two cases

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

    def server_opt(ip: str):
        return f"--server=https://{ip}:6443"

    k3s_token = get_parameter(K3S_SERVER_NAME + "/token")
    agent_public_ip = requests.get(
        "https://checkip.amazonaws.com", timeout=2
    ).text.strip()
    opts = [
        "--token=" + k3s_token,
        "--node-external-ip=" + agent_public_ip,
        "--node-label=lmrun=" + agent_label,
    ]

    if cloud.lower() == "aws":
        # not specifying public or private in server variable name to always return it
        server_ip = get_parameter(K3S_SERVER_NAME + "/ip/private")
        agent_private_ip = gethostbyname(gethostname())
        opts += ["--node-ip=" + agent_private_ip]
    else:
        server_ip = get_parameter(K3S_SERVER_NAME + "/ip/public")
        opts += ["--node-ip=" + agent_public_ip]
    opts += [server_opt(server_ip)]

    return opts, server_ip


def node_label(name: str):
    """Return a unique label to proxy service traffic targeting the VM"""
    # SKYPILOT_NUM_NODES isn't set on single-node clusters
    if os.environ.get("SKYPILOT_NUM_NODES", "1") == "1":
        return name
    return name + "-" + os.environ["SKYPILOT_SETUP_NODE_RANK"]


if __name__ == "__main__":
    cluster_info = json.loads(os.environ["SKYPILOT_CLUSTER_INFO"])
    cluster_name, cloud_name = cluster_info["cluster_name"], cluster_info["cloud"]
    label = node_label(cluster_name)

    k3s_command = ["curl", "-sfL", "https://get.k3s.io", "|", "sh", "-s", "-", "agent"]
    options, k3s_server_ip = connection_options(cloud_name, label)
    k3s_command += options
    run(" ".join(k3s_command), shell=True)

    port = read_port_arg()
    if port:
        print(f"Exposing a host service to the K3s cluster on port {port}..")
        kubeconfig = get_parameter(K3S_SERVER_NAME + "/kubeconfig")
        kube_dir = os.path.expanduser("~/.kube")
        os.makedirs(kube_dir, exist_ok=True)
        with open(os.path.join(kube_dir, "config"), "w", encoding="utf-8") as file:
            file.write(kubeconfig.replace("127.0.0.1", k3s_server_ip))
        host_service(label, port)
    else:
        print("Skipping service creation: --port isn't defined")
