# Workspace Compute
These templates run local code on remote GPUs (or other accelerators) attached to large storage. 

The setup is designed to support local development and code upload to execute. 
Thereby, you can leverage transient and cheap accelerators.

## Launch
Prerequisite: first 3 steps of the [Quickstart](/README.md#quickstart)
1. activate the Python environment in `..` (repo root) with `poetry shell`
2. `sky check` to verify cloud access - [doc](https://docs.skypilot.co/en/latest/getting-started/installation.html#verifying-cloud-access)
3. familiarize yourself with SkyPilot [Quickstart](https://docs.skypilot.co/en/latest/getting-started/quickstart.html#stop-terminate-a-cluster): see at least how to [stop](https://docs.skypilot.co/en/latest/getting-started/quickstart.html#stop-terminate-a-cluster) incurring costs for resources or plan to make use of [autostop](https://docs.skypilot.co/en/latest/reference/auto-stop.html)
4. Launching a L4 GPU while uploading a workdir is as simple as `sky launch -t g6.xlarge --workdir .`. Refer to Task [YAML](https://docs.skypilot.co/en/latest/reference/yaml-spec.html) and CLI [doc](https://docs.skypilot.co/en/latest/reference/cli.html#sky-launch) for all options.
5. then, `sky exec` can sync updated code and run it on the VM

## Templates
### Jupyter
Jupyter notebook server with GPU
1. `sky launch -c jupyter jupyter.yaml`
2. wait for the access URL `http://localhost:8888/tree?token=...` to appear in logs, copy it and type Ctrl-C to exit, the server will keep running in the background
3. redirect Jupyter default port `ssh -L 8888:localhost:8888 jupyter` 
4. paste the access URL in a browser