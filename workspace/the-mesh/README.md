# LMRun Cluster Mesh
This walkthrough showcases the LMRun mesh. Its network combines the power of service discovery in Kubernetes with the ease of use of a VM for AI workloads. Instances in any region or cloud automatically join the LMRun environment through VPN tunnels or peered VPCs.

---

We first [connect](#service--client-vms) distributed workloads through the mesh by running a benchmark task from LiveBench against a model server. We then introduce [managed jobs](#managed-spot-jobs) to help with further automation. We add LLM [observability](#stateful-and-ui-servers) to the mesh to show how any other MLOps interface would work. Finally, we demonstrate these features in a [multi-cloud](#multicloud-integration) context. 

*Prerequisite*: the main K3s cluster node must be up and running. Check with `sky status`. Otherwise, go to `/service` and run `sky launch -c main main.yaml` to launch the main node. Its setup creates credentials allowing new nodes (K3s agents) to join the cluster.

## Service & Client VMs
- A service VM exposes a port to the LMRun mesh. Do not confuse with SkyPilot clusters. The word *cluster* is context-dependent because LMRun is a cluster of SkyPilot clusters. Whenever possible, we use the word *mesh* to mean the LMRun cluster. 
- A client VM connects to a service VM.

### Network Topology 
**TL;DR**: CPU clients, middleware and services run in the main AWS region defined by `AWS_DEFAULT_REGION` in `.env` while the multi-cloud GPU fleet is globally distributed.

> Regional VPCs are only peered with the main region and peering connections are not transitive (VPC A and B are not connected when both peered with C). Therefore, to establish direct node connections within a global, yet private, AWS network, one of the 2 connected nodes must be in the main region. Outside AWS, nodes join the cluster through VPN tunnels attached to public IPs. Internally, communication works the same for all nodes: services expose special Kubernetes pod endpoints mapping to individual VMs. 

### Creating a service
In the setup section of `vllm-server.yaml`, we append `--app-port 8000 --node-port 30300` to the cluster agent command `sudo -E ./k3s_agent.py` to map and expose a port as a VM service. While vLLM default port `8000` can remain the same across servers, node port must be in the range `30000-32767` and unique on the entire LMRun mesh.

- Execute the first command below to launch a default model on the K3s cluster: 
```bash
# launch a default model defined in the yaml task as a mesh service
sky launch vllm-server.yaml -c qwen-coder
# alternative command overriding default model arguments
sky launch vllm-server.yaml --env MODEL=NovaSky-AI/Sky-T1-32B-Preview \
    --env VERSION=1e3f4c62a30c7ce70f4b3a3b952895d866943551 -c sky-t1
```

### Connecting to a service
You only need to know the node port of a service to connect to it because its address is `localhost:<NODE PORT>`. The cluster routes traffic to the right host from this port.

In our example, the server address is `localhost:30300`. Clients refer to it to reconstruct the vLLM server's API base `http://localhost:30300/v1`. Since OpenAI API specification requires a model name in inference requests, we add a `MODEL` variable. It's derived from SkyPilot server name (`-c` in `sky launch`) and set by `--served-model-name` in `vllm serve` on the server. 
```bash
sky launch -c client livebench-client.yaml --env SERVER=30300 --env MODEL=qwen-coder
```
Take instances down once the task completed and displayed results: `sky down qwen-coder client`.

## Managed Spot Jobs
*Prerequisite*: to spare an extra example VM, the next 2 sections require a new main node which includes a Phoenix server to trace LLM calls. Make sure that no node already exists with `sky status` and `sky down`. Then, start the main cluster node with `sky launch -c main main-phoenix.yaml` from `/service` folder.

Cost-effective spot instances running above models can be terminated. SkyPilot jobs automatically handle recovery thanks to a managed controller VM. In earlier examples, we decoupled client and server on different VMs. This useful pattern can query several LLMs from a single workload or expose the model to several clients. In this example, we demonstrate the same task on a single VM to showcase..

1. Stateful recovery when all processes are interrupted
- Notice we added the `--resume` flag to `gen_api_answer.py` in the job definition: the process must be configured to automatically restart where it stopped
- Launch the default job with the first command below: we run `sky jobs launch` instead of `sky launch` to turn a task into a managed job
```bash
# launch the default job defined in the yaml task
sky jobs launch monolithic-job.yaml -c qwen-coder
# launch the benchmarking job on any model fitting defined accelerators
sky jobs launch monolithic-job.yaml -c sky-t1 \
    --env MODEL=NovaSky-AI/Sky-T1-32B-Preview \
    --env VERSION=1e3f4c62a30c7ce70f4b3a3b952895d866943551
```
- At least a minute after a few benchmark questions completed, go to the AWS console and terminate the node to test recovery
- Data is backed up every minute and then synced at bootstrap (see `rsync` commands in `monolithic-job.yaml`): the LiveBench `data` folder will be recovered when the evaluation starts again where it stopped on the previous VM

2. How to integrate an LLM observability platform through the mesh: see Stateful and UI Servers below

## Stateful and UI Servers
- Access a UI: redirect the port, in this case Phoenix, to your local machine `ssh -L 6006:localhost:6006 main` and visit `localhost:6006` in your browser.
- `monolithic-job.yaml` populates a LiveBench project in Phoenix. Besides telemetry dependencies (`arize`, `openinference`) and the initialization injected from `sitecustomize.py`, the only required configuration is `PHOENIX_GRPC_PORT: 30201`, which specifies the node port `30201` for the gRPC endpoint `4317` defined in `main-phoenix.yaml`: `--app-ports 6006,4317 --node-ports 30200,30201`. Ports map in order and the first is Phoenix UI. 
- Stop the main node with `sky stop` if you'd like to preserve data at rest without having to back up. You could also run `rsync` from `~/.phoenix` to `/r2/` before shutting down and vice versa next time you need to load this data.

> Any MLOps platform running on a VM can connect to the mesh thanks to `k3s_agent.py` flags: `--app-port(s)` maps to exposed `--node-port(s)`. As a result, clients connect to servers across the global and private LMRun mesh through a `localhost:<NODE PORT>` URL.

## Multicloud Integration
### Configuration
1. UDP port `51820` must be open on the VM to connect to the LMRun mesh via VPN: 
on Lambda Cloud, firewall settings are configured once at an account level.
2. By default, LMRun doesn't let SkyPilot share local AWS secrets with any VM. Outside AWS, the task definition should mount least privilege permissions created by the mesh stack, as shown below.

```yaml
file_mounts:
  ~/.aws/credentials: ~/.aws/ext-vm-credentials
```

### Example
This example is a common use case: we launch a model on an external GPU provider to interact with it from an existing environment on a hyperscaler.

We'll deploy a model on Lambda and chat with it from Open WebUI, a user-friendly interface, hosted on an AWS instance. The LMRun mesh integrates both nodes seamlessly over a secure cluster network.

*Prerequisites*: 
- Follow SkyPilot [doc](https://docs.skypilot.co/en/latest/getting-started/installation.html#lambda-cloud) to set up your Lambda Cloud key.
- Go to Lambda firewall [settings](https://cloud.lambdalabs.com/firewall) and create a new inbound rule for the VPN connection: select "Custom UDP" type and enter port `51820`. Leaving default source `0.0.0.0/0` is safe (check out WireGuard VPN if you'd like to know more). 
- Start a new LMRun cluster from scratch. First, make sure that no node already exists with `sky status` and `sky down`. Then, start the main cluster node with `sky launch -c main main-webui.yaml` from `/service` folder.

1. Launch Qwen coder on Lambda Cloud: `sky launch -c qwen-coder external-server.yaml`
2. Redirect Open WebUI port `ssh -L 8080:localhost:8080 main` and visit `localhost:8080` in your browser to add the model you just deployed: click on the top-right user icon > Admin Panel > Settings tab > Connections > + to add an "OpenAI API Connection" > enter `http://localhost:30300/v1` as URL, a random placeholder as key, and click Save. `30300` is defined by `--node-port` in `external-server.yaml`.
3. Click on New Chat top-left to experience this AI environment over 2 clouds.