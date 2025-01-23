# LMRun Cluster Mesh
These templates showcase the LMRun mesh. It combines the power of service discovery in Kubernetes with the ease of use of a VM for AI workloads. Any VM in any region and on any cloud can join the mesh.

---

We first [connect](#service--client-vms) example workloads below by running a benchmark task from LiveBench against a model server. We then introduce [managed jobs](#managed-spot-jobs) to help with further automation. We add LLM [observability](#stateful-services) to the mesh to show how any other MLOps interface would work. Finally, we demonstrate these features in a [multi-cloud](#multicloud-mesh) context. 

*Prerequisite*: the main K3s cluster node must be up and running. Check with `sky status`. Otherwise, go to `service` and run `sky launch -c main main.yaml` to launch the main node. Its setup creates credentials allowing new nodes (K3s agents) to join the cluster.

## Service & Client VMs
- A service VM exposes a port to the LMRun mesh. Do not confuse with SkyPilot clusters. The word 'cluster' is context-dependent because LMRun is a cluster of SkyPilot clusters. Whenever possible, we use the word 'mesh' to mean the LMRun cluster. 
- A client VM connects to a service VM.

### Network Topology 
**TL;DR**: CPU clients, middleware and services run in the main AWS region defined by `AWS_DEFAULT_REGION` in `.env` while the multi-cloud GPU fleet is globally distributed.

> Regional VPCs are only peered with the main region and peering connections are not transitive (VPC A and B are not connected when both peered with C). Therefore, to establish direct node connections within a global, yet private, AWS network, one of the 2 connected nodes must be in the main region. Outside AWS, nodes join the cluster through VPN tunnels attached to public IPs and connect to Kubernetes pod IPs mapping to individual VMs. 

### Creating a service
In the setup section of `model-server.yaml`, we append `--port 8000` to the cluster agent command `sudo -E ./k3s_agent.py` to expose a port as a VM service, in this case vLLM. The SkyPilot name for the server VM, `-c` in `sky launch`, is reused to name the service.

- Execute `./launch-32B.sh qwen-coder` to launch a default model on the K3s cluster. The script is a simple wrapper around `model-server.yaml`. To launch another model, you can override or edit default arguments, or use the CLI:
```bash
sky launch model-server.yaml --env MODEL=NovaSky-AI/Sky-T1-32B-Preview \
    --env VERSION=1e3f4c62a30c7ce70f4b3a3b952895d866943551 -c sky-t1
```

### Connecting to a service
By default, you only need to know the name of a service to connect to it because its address is `<SERVICE NAME>.default.svc.cluster.local`. However, when `k3s_agent.py` is configured with `--namespace` in addition to `--port`, this namespace maps to the URL subdomain and replaces `default`.   

In the first example, the server address is `qwen-coder.benchmark.svc.cluster.local`. The client reconstructs the vLLM server's API base `http://$SERVER.$DOMAIN.svc.cluster.local:8000/v1` from these 2 variables `SERVER` and `DOMAIN`.
```bash
sky launch -c client livebench-client.yaml --env SERVER=qwen-coder --env DOMAIN=benchmark
```
Take VMs down once the task completed and displayed results: `sky down qwen-coder client`.

## Managed Spot Jobs
Efficient spot instances used to run models above can be terminated. SkyPilot jobs automatically handle recovery thanks to a managed controller VM. In earlier examples, we decoupled client and server on different VMs. This useful pattern can query several LLMs from a single workload. In this example, we demonstrate the same task on a single VM to showcase..

1. stateful recovery when all processes are interrupted
- notice we added the `--resume` flag to `gen_api_answer.py` in the job definition: the process must be configured to automatically restart where it stopped
- launch with `./launch-32B.sh qwen-coder monolithic-job.yaml`: the script runs `sky jobs launch` instead of `sky launch` to turn a task into a managed job
```bash
# CLI command to launch a benchmarking job on any model fitting defined accelerators
sky jobs launch monolithic-job.yaml -c sky-t1 \
    --env MODEL=NovaSky-AI/Sky-T1-32B-Preview \
    --env VERSION=1e3f4c62a30c7ce70f4b3a3b952895d866943551
```
- at least a minute after a few benchmark questions completed, go to the AWS console and terminate the node to test recovery
- data is backed up every minute and then synced at bootstrap (see `rsync` commands in `monolithic-job.yaml`): the LiveBench `data` folder will be recovered when the evaluation starts again where it stopped on the previous VM

2. how to integrate an LLM observability platform through the mesh: see Stateful Services below

## Stateful Services
*coming soon*

- Proxy the UI
- Stop but do not shut down these services to preserve data at rest.

## Multicloud Mesh
*coming soon*
