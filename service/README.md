# Sky Services
> multi-cloud MLOps services

Check out [/workspace/the-mesh](/workspace/the-mesh) for examples working with services.

Any VM initialized with `k3s_server.py` is a main K3s node. Any VM initialized with `k3s_agent.py` is a K3s agent. There is only a single active main node at a time and new agents connect to the most recent. The main node should always be provisioned first and decommissioned last to preserve the LMRun cluster integrity. Finally, security groups and agents expect a main node launched with `sky launch -c main`. This name is matched in `~/.sky/config.yaml` and defined by `K3S_SERVER_NAME` in `k3s_agent.py`. 

`k3s_*` bootstrap scripts can be found in `/setup` and live versions are in the R2 bucket. Sync with `/setup/r2-sync.sh`.

## K3s servers
> pick a single main node or extend `main.yaml` with a custom service

- `sky launch -c main main.yaml` to launch a minimal main K3s node
- `sky launch -c main main-phoenix.yaml` to include a [Phoenix](https://phoenix.arize.com) server cohosted with the main K3s node
- `sky launch -c main main-webui.yaml` to include a cohosted [Open WebUI](https://docs.openwebui.com) server

## K3s agents
- `phoenix-webui.yaml` cohosts Open WebUI and Phoenix servers. Typically, this agent connects to a minimal K3s server like `main.yaml` to join the service mesh and expose 3 ports: WebUI to chat with models and Phoenix UI + gRPC endpoint for LLM traces.

## Fixed private IPs
*power users*

<details>

The Kubernetes DNS system integrated with VMs covers all use cases but requires a K3s server. It's still possible to assign a known private IP to an AWS instance without a running K3s server. The mesh stack creates a private network interface in each zone of the main region (6 in us-east-1). Note that the associated IPs don't work across clouds.

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
2. Attach the network interface to your instance in the same zone. By default, network interfaces are listed in [us-east-1.console.aws.amazon.com/ec2/home#NIC](https://us-east-1.console.aws.amazon.com/ec2/home#NIC). Attaching the network interface to an instance isn't handled by LMRun.
3. Configure this fixed IP in internal clients. It is always `10.4.x.4` where `x` is the subnet block: one of `0`, `32`, `64`, `96`, `128` or `160`.
```yaml
envs:
  # see zone in <server>.yaml to determine the subnet, e.g. 10.4.0.x
  MLOPS_IP: 10.4.0.4  # always 5th IP (.4) in subnet
``` 
</details>