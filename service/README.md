# Sky Services
multi-cloud MLOps services

- `sky launch -c main main.yaml` to launch the main K3s cluster node

## Fixed private IPs
*power users only*

The Kubernetes DNS system integrated with VMs covers all use cases but requires a K3s server. It's still possible to assign a known private IP to an AWS instance without a running K3s server. The mesh stack creates a private network interface in each zone of the main region (6 in us-east-1).

1. Launch your server VM in a zone mapping to an IP.
```yaml
resources:
  cloud: aws
  # zone maps to subnet: adjust "MLOPS_IP" in internal clients accordingly
  # 'a' maps to 1st subnet 10.4.0.x in 10.4.x.x block
  # 'b' maps to 2nd subnet 10.4.32.x (/19 IP blocks)
  # 'c' maps to 3rd subnet 10.4.64.x
  # etc
  zone: us-east-1a  # zone to allocate a fixed IP
``` 
2. Attach the network interface to your instance in the same zone. By default, network interfaces are listed in [us-east-1.console.aws.amazon.com/ec2/home#NIC](https://us-east-1.console.aws.amazon.com/ec2/home#NIC).
3. Configure this fixed IP in internal clients. It is always `10.4.x.4` where `x` is the subnet block: one of `0`, `32`, `64`, `96`, `128` or `160`.
```yaml
envs:
  # see zone in <server>.yaml to determine the subnet, e.g. 10.4.0.x
  MLOPS_IP: 10.4.0.4  # always 5th IP (.4) in subnet
```

Note: how to attach the network interface to an instance is up to you. 