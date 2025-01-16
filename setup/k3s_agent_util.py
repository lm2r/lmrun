"""Utilities for K3s agent setup

Import with the main script in task setup: `install -m 755 /r2/setup/k3s_agent*`
"""

import os
import subprocess

host_service_template = """
apiVersion: v1
kind: Service
metadata:
  name: <LABEL>
spec:
  clusterIP: None  # headless service
  selector:
    app: <LABEL>
  ports:
    - port: <PORT>
      targetPort: <PORT>
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: <LABEL>
spec:
  serviceName: <LABEL>
  replicas: 1
  selector:
    matchLabels:
      app: <LABEL>
  template:
    metadata:
      labels:
        app: <LABEL>
    spec:
      nodeSelector:
        lmrun: <LABEL>
      hostNetwork: true  # returns the node IP instead of pod IP 
      terminationGracePeriodSeconds: 0
      containers:
      - name: proxy
        image: registry.k8s.io/pause:3.9  # first pod container (480KB) doing nothing
        ports:
        - containerPort: <PORT>
          hostPort: <PORT>  # maps to the port on the node
          protocol: TCP
"""


def run(command: list[str] | str, shell=False):
    """Run a shell command from a list of strings, unless shell=True:
    i.e. command is a string and special characters are interpreted in a shell"""
    try:
        output = subprocess.run(
            command, shell=shell, check=True, capture_output=True, text=True
        )
        # commands like `systemctl restart` don't produce output unless they error out
        if output.stdout:
            print("STDOUT:", output.stdout)
    except subprocess.CalledProcessError as e:
        print("STDERR:", e.stderr)
        raise e


def k3s_dns():
    """Set up kubernetes nameserver for cluster endpoints on the host"""
    conf_dir = "/etc/systemd/resolved.conf.d/"
    content = "[Resolve]\nDNS=10.43.0.10\nDomains=~cluster.local\n"
    os.makedirs(conf_dir, exist_ok=True)
    with open(conf_dir + "k3s-dns.conf", "w", encoding="utf-8") as file:
        file.write(content)
    run(["systemctl", "restart", "systemd-resolved"])


def host_service(host_label: str, port: int):
    """Expose a host service to the K3s cluster on specified port"""
    service_yaml = host_service_template.replace("<LABEL>", host_label).replace(
        "<PORT>", str(port)
    )
    print(f"Exposing a host service to the K3s cluster on port {port}..")
    run(f'echo "{service_yaml}" | kubectl apply -f -', shell=True)


def cleanup_command(label: str):
    """
    1. Count how many nodes match the label
    2. If there are 2 or more nodes:
      - Get the nodes sorted by creation timestamp
      - Select the oldest one
      - Delete that node
    """
    selector = f"kubectl get nodes -l lmrun={label} --no-headers"
    return f"""if [ $({selector} | wc -l) -ge 2 ]; then
        {selector} --sort-by=.metadata.creationTimestamp \
          -o custom-columns=NAME:.metadata.name | 
        head -1 | 
        xargs kubectl delete node
    fi
    """
