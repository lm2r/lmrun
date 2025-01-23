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
  clusterIP: None  # headless service
  selector:
    app: <LABEL>
  ports:
"""
# spec.ports[*].name is required for more than one port
service_port_template = """
    - port: <PORT>
      targetPort: <PORT>
      name: '<PORT>'
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
      hostNetwork: true  # returns the node IP instead of pod IP
      terminationGracePeriodSeconds: 0
      containers:
      - name: proxy
        image: registry.k8s.io/pause:3.9  # first pod container (480KB) doing nothing
        ports:
"""
statefulset_port_template = """
        - containerPort: <PORT>
          hostPort: <PORT>  # maps to a port on the node
          protocol: TCP
"""


def build_manifest(host_label: str, ports: str, namespace: str):
    """Render and combine Kubernetes object templates to return the final manifest"""
    namespace_manifest = namespace_template.replace("<NAMESPACE>", namespace)
    svc_manifest = service_template.replace("<NAMESPACE>", namespace).replace(
        "<LABEL>", host_label
    )
    sts_manifest = statefulset_template.replace("<NAMESPACE>", namespace).replace(
        "<LABEL>", host_label
    )

    for port in ports.split(","):
        svc_manifest += service_port_template.replace("<PORT>", port)
        sts_manifest += statefulset_port_template.replace("<PORT>", port)

    manifest = "---\n".join([namespace_manifest, svc_manifest, sts_manifest])
    # remove blank lines to clean output
    return manifest.replace("\n\n", "\n").strip()
