# Workspace Compute
These templates run local code on remote GPUs (or other accelerators) attached to large storage. 

The setup is designed to support local development and code upload to execute. 
Thereby, it leverages transients and cheap accelerators.

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

### OpenAI Compatible Servers
These templates show patterns to run language models easily. At their core, [vLLM](https://github.com/vllm-project/vllm) provides an efficient LLM server that implements OpenAI's API. We use various sizes of the same coding model to illustrate use cases.

*Prerequisite*: R2 storage configuration (see section further below)

Let's declare a Hugging Face repo: `MODEL=Qwen/Qwen2.5-Coder-7B-Instruct`

- **Model Download**

`sky launch model-download.yaml --env REPO=$MODEL -i 5 --down`

The model will be saved in a R2 bucket, ready to be served globally from object storage. `-i 5 --down` takes the server down after it's been 5 minutes idle.

## Cloudflare R2 storage
If you're already familiar with S3, R2 is a more efficient substitute for LMRun global architecture, even when compute is provided by AWS.

1. For access to data or models on object storage, you will need a Cloudflare account with a payment method for R2, which won't be used within the free tier.
2. On Cloudflare, go to “R2 Object Storage” in the left-side menu > “Create bucket” > Call it “lmrun” and click “Create bucket”.
3. Configure R2 as described in SkyPilot [doc](https://docs.skypilot.co/en/latest/getting-started/installation.html#cloudflare-r2). When creating the API token, restrict permissions to "Object Read & Write" and apply to the `lmrun` bucket only. Note that all values you need, incl. the Cloudflare Account ID, are on the final screen. The account is the first part of the URL in `https://<Your Account ID>.r2.cloudflarestorage.com`.
4. Check your configuration with `sky check`: the command should output this line "Cloudflare (for R2 object store): enabled" in green.