# Workspace Compute
These templates run local code on remote GPUs (or other accelerators) with access to large storage. 

They upload code to leverage transients and cheap accelerators.

## Launch
Prerequisite: first 3 steps of the [Quickstart](/README.md#quickstart)
1. activate the Python environment with `poetry shell`
2. `sky check` to verify cloud access - [doc](https://docs.skypilot.co/en/latest/getting-started/installation.html#verifying-cloud-access)
3. familiarize yourself with SkyPilot [Quickstart](https://docs.skypilot.co/en/latest/getting-started/quickstart.html#stop-terminate-a-cluster): see at least how to [stop](https://docs.skypilot.co/en/latest/getting-started/quickstart.html#stop-terminate-a-cluster) incurring costs for resources or plan to make use of [autostop](https://docs.skypilot.co/en/latest/reference/auto-stop.html)
4. Launching a L4 GPU while uploading a workdir is as simple as `sky launch -t g6.xlarge --workdir .`. Refer to Task [YAML](https://docs.skypilot.co/en/latest/reference/yaml-spec.html) and CLI [doc](https://docs.skypilot.co/en/latest/reference/cli.html#sky-launch) for all options.
5. then, `sky exec` can sync updated code and run it on the VM

## Templates
### Jupyter
Jupyter notebook server with GPU
1. `sky launch -c jupyter jupyter.yaml`
2. wait for the access URL `http://localhost:8888/tree?token=...` to appear in logs, copy it and type Ctrl-C to exit, the server will keep running in the background
3. redirect Jupyter default port while opening a shell on the server `ssh -L 8888:localhost:8888 jupyter` 
4. paste the access URL in a browser

### LLM Server
These templates show patterns to run language models easily. At their core, [vLLM](https://github.com/vllm-project/vllm) provides an efficient LLM server that implements OpenAI's API. We use various sizes of the same coding model to illustrate use cases.

*Prerequisite*: R2 storage configuration (see section further below)

Let's declare a Hugging Face repository and its latest commit hash:
```bash
MODEL=Qwen/Qwen2.5-Coder-7B-Instruct
# downloads pull the latest, it is then explicitly specified to run the model
VERSION=0eb6b1ed2d0c4306bc637d09ecef51e59d3dfe05
```
- **Download** and upload a model to an R2 bucket to use it:
```bash
sky launch model-download.yaml --env REPO=$MODEL -i 5 --down
```
The model will be ready to be served globally from object storage. `-i 5 --down` shuts down the server after 5 minutes of inactivity. Note that this job incurs AWS egress costs, typically $0.09/GB. Then, ingress to anywhere will be free.
- **Serve** the LLM you just staged, the version is in the R2 bucket path:
```bash
sky launch vllm.yaml --env MODEL=$MODEL --env VERSION=$VERSION -c vllm
```
- **Call** your LLM server:

To remain secure, this simple setup requires a SSH tunnel for remote requests: `ssh -L 8000:localhost:8000 vllm`. Example request from your local machine or on the server:
```
curl http://localhost:8000/v1/chat/completions -H "Content-Type: application/json" -d '{
  "model": "/r2/model/Qwen/Qwen2.5-Coder-7B-Instruct/0eb6b1ed2d0c4306bc637d09ecef51e59d3dfe05",
  "messages": [
    {"role": "system", "content": "You are a helpful code assistant."},
    {"role": "user", "content": "Can you keep coding while I grab a coffee?"}
  ]
}'
```
Any SDK compatible with OpenAI API works.

## Cloudflare R2 storage
If you're already familiar with S3, R2 is a more efficient substitute for LMRun global architecture, even when compute is provided by AWS.

1. For access to data or models on object storage, you will need a Cloudflare account with a payment method for R2, which won't be used within the free tier.
2. On Cloudflare, go to “R2 Object Storage” in the left-side menu > “Create bucket” > Call it “lmrun” and click “Create bucket”.
3. Configure R2 as described in SkyPilot [doc](https://docs.skypilot.co/en/latest/getting-started/installation.html#cloudflare-r2). When creating the API token, restrict permissions to "Object Read & Write" and apply to the `lmrun` bucket only. Note that all values you need, incl. the Cloudflare Account ID, are on the final screen. The account is the first part of the URL in `https://<Your Account ID>.r2.cloudflarestorage.com`.
4. Check your configuration with `sky check`: the command should output this line "Cloudflare (for R2 object store): enabled" in green.