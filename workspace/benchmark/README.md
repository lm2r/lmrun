# LMRun Cluster Mesh
These templates run a benchmark job from LiveBench against a model running on a different server to showcase the LMRun mesh: any VM in any region and on any cloud can connect to any other VM.

*Prerequisite*: the main K3s cluster node must be up and running. Check with `sky status`. Otherwise, go to `service` and run `sky launch -c main main.yaml` to launch the main node. Its setup creates credentials allowing new nodes (K3s agents) to join the cluster.

## Service & Client VMs
- A service VM exposes a port to the LMRun mesh. Do not confuse with SkyPilot clusters. The word 'cluster' is context-dependent because LMRun is a cluster of SkyPilot clusters. Whenever possible, we use the word 'mesh' to mean the LMRun cluster. 
- A client VM connects to a service VM.

 Latency is minimized when one of the two connected VMs runs in the AWS region defined by `AWS_DEFAULT_REGION` in `.env`. In practice, this means that CPU-based clients, middleware and services should run in the main region while the GPU fleet is globally distributed. 

### Creating a service
In the setup section of the server template `model-server.yaml`, we append `--port 8000` to the cluster agent command `sudo -E ./k3s_agent.py` to expose a port as a VM service, in this case vLLM. The SkyPilot name for the server VM, `-c` in `sky launch`, is reused to name the service. Inside `run-qwen-coder.sh` for example, the service will be named `qwen-coder`. 

- Execute `./run-qwen-coder.sh` or `./run-sky-t1.sh` to launch one of these 2 models on the K3s cluster. They wrap the `model-server.yaml` template.

### Connecting to a service
You only need to know the name of a service to connect to it because its address is `<SERVICE NAME>.default.svc.cluster.local`.

In the previous example, the server address will be `qwen-coder.default.svc.cluster.local`. That's why we only pass this name to the `SERVER` variable of the client.
```bash
sky launch -c client livebench-client.yaml --env SERVER=qwen-coder -i 5 --down
```
Take the server down once the task completed and displayed results: `sky down qwen-coder`.

## Managed Spot Jobs
*coming soon*

## Stateful Services
*coming soon*

- Stop but do not shut down these services to preserve data at rest.

## Multicloud Mesh
*coming soon*
