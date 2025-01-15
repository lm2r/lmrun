"""Utilities for K3s agent setup

Import with the main script in task setup: `install -m 755 /r2/setup/k3s_agent*`
"""

import subprocess

host_service_template = """
apiVersion: v1
kind: Service
metadata:
  name: <LABEL>
spec:
  clusterIP: None  # This makes it a headless service
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
      containers:
      - name: proxy
        image: registry.k8s.io/pause:3.9  # Minimal container that does nothing
        ports:
        - containerPort: <PORT>
          hostPort: <PORT>  # This maps to the port on the node
          protocol: TCP
"""


def run(command: list[str] | str, shell=False):
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


def host_service(host_label: str, port: int):
    """Expose a host service to the K3s cluster on specified port"""
    service_yaml = host_service_template.replace("<LABEL>", host_label).replace(
        "<PORT>", str(port)
    )
    run(f'echo "{service_yaml}" | kubectl apply -f -', shell=True)
