# LMRun Cluster Mesh
These templates showcase the LMRun mesh: it combines the power of service discovery in Kubernetes with the ease of use of a VM for AI workloads. Any VM in any region and on any cloud can join the mesh.

As a simple example, we connect CPU and GPU workloads by running a benchmark task from LiveBench against a model server.

*Prerequisite*: the main K3s cluster node must be up and running. Check with `sky status`. Otherwise, go to `service` and run `sky launch -c main main.yaml` to launch the main node. Its setup creates credentials allowing new nodes (K3s agents) to join the cluster.

## Service & Client VMs
- A service VM exposes a port to the LMRun mesh. Do not confuse with SkyPilot clusters. The word 'cluster' is context-dependent because LMRun is a cluster of SkyPilot clusters. Whenever possible, we use the word 'mesh' to mean the LMRun cluster. 
- A client VM connects to a service VM.

### Network Topology 
**TL;DR**: CPU clients, middleware and services run in the main AWS region defined by `AWS_DEFAULT_REGION` in `.env` while the multi-cloud GPU fleet is globally distributed.

> Regional VPCs are only peered with the main region and peering connections are not transitive (VPC A and B are not connected when both peered with C). Therefore, to establish direct node connections within a global, yet private, AWS network, one of the 2 connected nodes must be in the main region. Outside AWS, nodes join the cluster through VPN tunnels attached to public IPs and connect to Kubernetes pod IPs mapping to individual VMs. 

### Creating a service
In the setup section of the server template `model-server.yaml`, we append `--port 8000` to the cluster agent command `sudo -E ./k3s_agent.py` to expose a port as a VM service, in this case vLLM. The SkyPilot name for the server VM, `-c` in `sky launch`, is reused to name the service. Inside `run-qwen-coder.sh` for example, the service will be named `qwen-coder`. 

- Execute `./run-qwen-coder.sh` or `./run-sky-t1.sh` to launch one of these 2 models on the K3s cluster. These scripts are simple wrappers around `model-server.yaml`.

### Connecting to a service
By default, you only need to know the name of a service to connect to it because its address is `<SERVICE NAME>.default.svc.cluster.local`.

In the previous example, the server address will be `qwen-coder.default.svc.cluster.local`. That's why we only pass this name to the `SERVER` variable of the client.
```bash
sky launch -c client livebench-client.yaml --env SERVER=qwen-coder -i 5 --down
```
Take the server down once the task completed and displayed results: `sky down qwen-coder`.

## Managed Spot Jobs
*coming soon*

## Stateful Services
*coming soon*

- Proxy the UI
- Stop but do not shut down these services to preserve data at rest.

## Multicloud Mesh
*coming soon*
