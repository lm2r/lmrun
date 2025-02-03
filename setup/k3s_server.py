#!/usr/bin/env python3
"""K3s server bootstrap"""

import os
import json
from typing import Literal
import secrets
import string
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

firewall_filter(main_node=True)  # security first, dependent on apt_setup()

# prevent public node port exposure: only allow cluster CIDR
network_policy = """
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: lmrun
spec:
  podSelector: {}  # Empty podSelector matches all pods
  policyTypes:
    - Ingress
  ingress:
    - from:
        - ipBlock:
            cidr: 10.42.0.0/16
"""


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
    print(f"Put {name} in parameter store")
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


def connection_options() -> tuple[list[str], str]:
    """Set K3s command flags to connect agents"""
    opts = []

    k3s_token = generate_k3s_token()
    store_parameter(cluster_name + "/token", k3s_token, "SecureString", region)
    opts += ["--token=" + k3s_token]

    private_ip = get_private_ip()
    store_parameter(cluster_name + "/ip/private", private_ip, "String", region)

    public_ip = instance_metadata(slug="public-ipv4")
    store_parameter(cluster_name + "/ip/public", public_ip, "String", region)
    # tls-san adds the public ip to kubeconfig certificate to run kubectl outside AWS
    opts += ["--node-external-ip=" + public_ip, "--tls-san=" + public_ip]

    return opts, private_ip


if __name__ == "__main__":
    cluster_info = json.loads(os.environ["SKYPILOT_CLUSTER_INFO"])
    cluster_name, region = cluster_info["cluster_name"], cluster_info["region"]

    k3s_command = [
        "curl",
        "-sfL",
        "https://get.k3s.io",
        "|",
        "INSTALL_K3S_VERSION=" + K3S_VERSION,
        "sh",
        "-s",
        "-",
        "server",
        "--flannel-external-ip",
        "--flannel-backend=wireguard-native",
        "--write-kubeconfig-mode=644",
        "--cluster-domain=lm.run",
        "--node-label=lmrun=" + cluster_name,
    ]

    conn_opts, private_ip = connection_options()
    k3s_command += conn_opts
    run(" ".join(k3s_command), shell=True)

    # secure before service configuration
    run(f'echo "{network_policy}" | kubectl apply -f -', shell=True)
    service_config(cluster_name, private_ip)  # host label is cluster name on main node

    with open("/etc/rancher/k3s/k3s.yaml", "r", encoding="utf-8") as file:
        kubeconfig = file.read()
    store_parameter(cluster_name + "/kubeconfig", kubeconfig, "SecureString", region)
