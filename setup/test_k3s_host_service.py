"""Test manifest rendering in k3s_host_service.py"""


def test_build_manifest():
    """
    >>> print(manifest)
    apiVersion: v1
    kind: Namespace
    metadata:
      name: default
    ---
    apiVersion: v1
    kind: Service
    metadata:
      name: main
      namespace: default
      labels:
        lmrun: main
    spec:
      clusterIP: None  # headless service
      selector:
        app: main
      ports:
        - port: 6006
          targetPort: 6006
          name: '6006'
        - port: 4317
          targetPort: 4317
          name: '4317'
    ---
    apiVersion: apps/v1
    kind: StatefulSet
    metadata:
      name: main
      namespace: default
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
          hostNetwork: true  # returns the node IP instead of pod IP
          terminationGracePeriodSeconds: 0
          containers:
          - name: proxy
            image: registry.k8s.io/pause:3.9  # first pod container (480KB) doing nothing
            ports:
            - containerPort: 6006
              hostPort: 6006  # maps to a port on the node
              protocol: TCP
            - containerPort: 4317
              hostPort: 4317  # maps to a port on the node
              protocol: TCP
    """


if __name__ == "__main__":
    import doctest
    from k3s_host_service import build_manifest

    manifest = build_manifest("main", "6006,4317", "default")
    doctest.testmod()
