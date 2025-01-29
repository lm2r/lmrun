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
          hostNetwork: true
          terminationGracePeriodSeconds: 0
          containers:
          - name: proxy
            image: registry.k8s.io/pause:3.9  # first pod container (480KB) doing nothing
            ports:
            - containerPort: 6006
              hostPort: 6006  # maps to service running on the VM
              protocol: TCP
            - containerPort: 4317
              hostPort: 4317  # maps to service running on the VM
              protocol: TCP
    """


if __name__ == "__main__":
    import doctest
    from k3s_host_service import build_manifest

    manifest = build_manifest("main", ["6006", "4317"], ["30006", "30317"], "test")
    doctest.testmod()
