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

# for the reverse proxy to work, local network != cluster CIDR: 10.42.0.0/16
configmap_template = """
apiVersion: v1
kind: ConfigMap
metadata:
  name: <LABEL>
  namespace: <NAMESPACE>
  labels:
    lmrun: <LABEL>
data:
  nginx.conf: |
    events {}
    http {
        server {
<LISTENERS>
            location / {
                proxy_pass http://<PRIVATE_IP>:\$server_port;
                proxy_set_header Host \$host;
                proxy_set_header X-Real-IP \$remote_addr;
            }
        }
    }
"""
configmap_port_template = """
            listen <APP_PORT>;
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
      hostNetwork: false  # must be false to route node-to-node communication over VPN
      terminationGracePeriodSeconds: 0
      volumes:
      - name: config
        configMap:
          name: <LABEL>
      containers:
      - name: proxy
        image: nginx:1.27.4-alpine-slim
        volumeMounts:
        - name: config
          mountPath: /etc/nginx/nginx.conf
          subPath: nginx.conf
        ports:
"""
statefulset_port_template = """
        - containerPort: <APP_PORT>
"""


def build_manifest(
    host_label: str,
    private_ip: str,
    app_ports: list[str],
    node_ports: list[str],
    namespace: str,
) -> str:
    """Render and combine Kubernetes object templates to return the final manifest"""
    assert len(app_ports) == len(node_ports), (
        f"Missing port to match app ({app_ports}) and node ({node_ports}) ports"
    )

    svc_manifest, sts_manifest = service_template, statefulset_template
    nginx_listeners = ""
    for app_port, node_port in zip(app_ports, node_ports):
        svc_manifest += service_port_template.replace("<APP_PORT>", app_port).replace(
            "<NODE_PORT>", node_port
        )
        sts_manifest += statefulset_port_template.replace("<APP_PORT>", app_port)
        nginx_listeners += configmap_port_template.replace("<APP_PORT>", app_port)

    manifest = (
        "---\n".join(
            [namespace_template, svc_manifest, configmap_template, sts_manifest]
        )
        .replace("<NAMESPACE>", namespace)
        .replace("<LABEL>", host_label)
        .replace("<LISTENERS>", nginx_listeners)
        .replace("<PRIVATE_IP>", private_ip)
    )
    return manifest.replace("\n\n", "\n").strip()  # remove blank lines for doctest
