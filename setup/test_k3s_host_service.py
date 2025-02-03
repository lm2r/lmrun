"""Test manifest rendering in k3s_host_service.py"""


def test_build_manifest():
    """
    >>> print(manifest)
    apiVersion: v1
    kind: Namespace
    metadata:
      name: test
    ---
    apiVersion: v1
    kind: Service
    metadata:
      name: main
      namespace: test
      labels:
        lmrun: main
    spec:
      type: NodePort
      selector:
        app: main
      ports:
        - port: 6006
          targetPort: 6006
          name: '6006'
          nodePort: 30006
        - port: 4317
          targetPort: 4317
          name: '4317'
          nodePort: 30317
    ---
    apiVersion: v1
    kind: ConfigMap
    metadata:
      name: main
      namespace: test
      labels:
        lmrun: main
    data:
      nginx.conf: |
        events {}
        http {
            server {
                listen 6006;
                listen 4317;
                location / {
                    proxy_pass http://10.4.0.4:\$server_port;
                    proxy_set_header Host \$host;
                    proxy_set_header X-Real-IP \$remote_addr;
                }
            }
        }
    ---
    apiVersion: apps/v1
    kind: StatefulSet
    metadata:
      name: main
      namespace: test
      labels:
        lmrun: main
    spec:
      serviceName: main
      replicas: 1
      selector:
        matchLabels:
          app: main
      template:
        metadata:
          labels:
            app: main
        spec:
          nodeSelector:
            lmrun: main
          hostNetwork: false  # must be false to route node-to-node communication over VPN
          terminationGracePeriodSeconds: 0
          volumes:
          - name: config
            configMap:
              name: main
          containers:
          - name: proxy
            image: nginx:1.27.4-alpine-slim
            volumeMounts:
            - name: config
              mountPath: /etc/nginx/nginx.conf
              subPath: nginx.conf
            ports:
            - containerPort: 6006
            - containerPort: 4317
    """


if __name__ == "__main__":
    import doctest
    from k3s_host_service import build_manifest

    manifest = build_manifest(
        "main", "10.4.0.4", ["6006", "4317"], ["30006", "30317"], "test"
    )
    doctest.testmod()
