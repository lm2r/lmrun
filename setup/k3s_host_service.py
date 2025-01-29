"""Kubernetes manifest templates to set up cluster-wide discovery of host services"""

namespace_template = """
apiVersion: v1
kind: Namespace
metadata:
  name: <NAMESPACE>
"""

service_template = """
apiVersion: v1
kind: Service
metadata:
  name: <LABEL>
  namespace: <NAMESPACE>
  labels:
    lmrun: <LABEL>
spec:
  type: NodePort
  selector:
    app: <LABEL>
  ports:
"""
# spec.ports[*].name is required for more than one port
service_port_template = """
    - port: <APP_PORT>
      targetPort: <APP_PORT>
      name: '<APP_PORT>'
      nodePort: <NODE_PORT>
"""

statefulset_template = """
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: <LABEL>
  namespace: <NAMESPACE>
  labels:
    lmrun: <LABEL>
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
      hostNetwork: true
      terminationGracePeriodSeconds: 0
      containers:
      - name: proxy
        image: registry.k8s.io/pause:3.9  # first pod container (480KB) doing nothing
        ports:
"""
statefulset_port_template = """
        - containerPort: <APP_PORT>
          hostPort: <APP_PORT>  # maps to service running on the VM
          protocol: TCP
"""


def build_manifest(
    host_label: str, app_ports: list[str], node_ports: list[str], namespace: str
) -> str:
    """Render and combine Kubernetes object templates to return the final manifest"""
    assert len(app_ports) == len(node_ports), (
        f"Missing port to match app ({app_ports}) and node ({node_ports}) ports"
    )

    namespace_manifest = namespace_template.replace("<NAMESPACE>", namespace)
    svc_manifest = service_template.replace("<NAMESPACE>", namespace).replace(
        "<LABEL>", host_label
    )
    sts_manifest = statefulset_template.replace("<NAMESPACE>", namespace).replace(
        "<LABEL>", host_label
    )

    for app_port, node_port in zip(app_ports, node_ports):
        svc_manifest += service_port_template.replace("<APP_PORT>", app_port).replace(
            "<NODE_PORT>", node_port
        )
        sts_manifest += statefulset_port_template.replace("<APP_PORT>", app_port)

    manifest = "---\n".join([namespace_manifest, svc_manifest, sts_manifest])
    # remove all blank lines for clean logging and doctest
    return manifest.replace("\n\n", "\n").strip()
