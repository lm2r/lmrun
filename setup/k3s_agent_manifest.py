"""Kubernetes manifest to set up cluster-wide discovery of host services

Import with the main script in task setup: `install -m 755 /r2/setup/k3s_agent*`
"""

host_service_template = """
apiVersion: v1
kind: Namespace
metadata:
  name: <NAMESPACE>
---
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
    - port: <PORT>
      targetPort: <PORT>
---
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
        - containerPort: <PORT>
          hostPort: <PORT>  # maps to the port on the node
          protocol: TCP
"""
