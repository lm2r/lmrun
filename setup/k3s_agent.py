#!/usr/bin/env python3
"""K3s agent bootstrap"""

import os
import json
import requests
from k3s_command import (
    K3S_VERSION,
    run,
    service_config,
    apt_setup,
    get_private_ip,
    firewall_filter,
)

apt_setup()  # includes boto3 install
import boto3  # noqa: E402

firewall_filter(main_node=False)  # security first, dependent on apt_setup()

K3S_SERVER_NAME = "main"


def get_parameter(suffix: str) -> str:
    """Get server parameters to connect K3s agents"""
    name = f"/lmrun/{suffix}"
    print(f"Get {name} from parameter store")
    # no region_name, relying on AWS_DEFAULT_REGION where the server is located
    return boto3.client("ssm").get_parameter(
        Name=name,
        # ignored for String and StringList parameter types
        WithDecryption=True,
    )["Parameter"]["Value"]


def connection_options(cloud: str, agent_label: str) -> tuple[list[str], str, str]:
    """Set K3s command flags to configure one of these two cases

    ## 1. private connectivity (on AWS)
    k3s agent \
    --node-external-ip=<AGENT_EXTERNAL_IP> \
    --node-ip=<AGENT_INTERNAL_IP> \
    --server https://<SERVER_INTERNAL_IP>:6443

    ## 2. public connectivity (not on AWS): no --node-ip (private)
    k3s agent \
    --node-external-ip=<AGENT_EXTERNAL_IP> \
    --server https://<SERVER_EXTERNAL_IP>:6443
    """

    def server_opt(ip: str) -> str:
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

    agent_private_ip = get_private_ip()
    if cloud.lower() == "aws":
        # not specifying public or private in server variable name to always return it
        server_ip = get_parameter(K3S_SERVER_NAME + "/ip/private")
        opts += ["--node-ip=" + agent_private_ip]
    else:
        server_ip = get_parameter(K3S_SERVER_NAME + "/ip/public")
    opts += [server_opt(server_ip)]

    return opts, server_ip, agent_private_ip


def node_label(name: str) -> str:
    """Return a unique label to proxy service traffic targeting the VM"""
    # SKYPILOT_NUM_NODES isn't set on single-node clusters
    if os.environ.get("SKYPILOT_NUM_NODES", "1") == "1":
        return name
    return name + "-" + os.environ["SKYPILOT_SETUP_NODE_RANK"]


def dupe_node_cleanup(label: str):
    """
    - Get nodes tagged with the label, sorted by creation timestamp
    - Select all nodes but the most recent (head -n -1)
    - Delete them if status is NotReady
    - If no duplicate node, silence the error (2>&-) and catch code 123
    """
    print(f"Checking for previous nodes with label lmrun={label}..")
    run(
        f"""kubectl get nodes -l lmrun={label} \
        --no-headers \
        --sort-by=.metadata.creationTimestamp | 
        head -n -1 | 
        awk '$2=="NotReady"{{print $1}}' | 
        xargs kubectl delete node 2>&- || 
        ([ $? = 123 ] && echo No duplicate node)""",
        shell=True,
    )


if __name__ == "__main__":
    cluster_info = json.loads(os.environ["SKYPILOT_CLUSTER_INFO"])
    cluster_name, cloud_name = cluster_info["cluster_name"], cluster_info["cloud"]
    label = node_label(cluster_name)

    k3s_command = [
        "curl",
        "-sfL",
        "https://get.k3s.io",
        "|",
        "INSTALL_K3S_VERSION=" + K3S_VERSION,
        "sh",
        "-s",
        "-",
        "agent",
    ]
    options, k3s_server_ip, this_private_ip = connection_options(cloud_name, label)
    k3s_command += options
    run(" ".join(k3s_command), shell=True)

    kubeconfig = get_parameter(K3S_SERVER_NAME + "/kubeconfig")
    kube_dir = os.path.expanduser("~/.kube")
    os.makedirs(kube_dir, exist_ok=True)
    with open(os.path.join(kube_dir, "config"), "w", encoding="utf-8") as file:
        file.write(kubeconfig.replace("127.0.0.1", k3s_server_ip))

    # delete previous records of the same node, if any, to clean and free service pods
    dupe_node_cleanup(label)
    service_config(label, this_private_ip)
