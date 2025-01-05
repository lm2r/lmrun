# Workspace Compute
These templates extend a local development environment with remote GPUs (or other accelerators) and storage. 

## Launch
*Prerequisite*: first 3 steps of the [Quickstart](/README.md#quickstart)
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
Two different sizes of the same model illustrate an ideal solution to bring data and models to compute at different scales. These templates also show patterns to run language models on any infrastructure. At their core, [vLLM](https://github.com/vllm-project/vllm) provides an efficient LLM server that implements OpenAI's API.

*Prerequisite*: R2 storage [configuration](#cloudflare-r2-storage)

#### Regular Throughput: R2, incl. small models
*small ~ 16-GiB model (tested 8B), up to 50 GiB depending on throttle tolerance*
> Bigger models (>= 50 GiB, tested 32B, limit may be lower) require premium storage distribution with the more generic `vllm.yaml` template in section further below.

Let's declare a Hugging Face repository and its latest commit hash:
```bash
MODEL=Qwen/Qwen2.5-Coder-7B-Instruct
# uploads push the latest, the version is then explicitly specified to run the model
VERSION=0eb6b1ed2d0c4306bc637d09ecef51e59d3dfe05
```
- **Upload** a model to an R2 bucket to make it available for global inference. 
```bash
sky launch hf-to-r2.yaml --env REPO=$MODEL -i 5 --down
```
`-i 5 --down` shuts down the upload server after 5 minutes of inactivity. Typically, the model would be custom or private. Otherwise, load it directly from Hugging Face with `vllm.yaml`, like the spot instance example below.
- **Serve** the LLM you just staged, the version is in the R2 bucket path. `vllm-7B.yaml` is only suitable for small models, as they're loaded through a mounted R2 bucket with limited throughput above this transfer size (Cloudflare runs smaller models on the edge):
```bash
sky launch vllm-7B.yaml --env MODEL=$MODEL --env VERSION=$VERSION -c vllm
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

### Sustained Throughput: Hugging Face, incl. spot instance demo
They are two ways to run workloads on cheap but preemptible VMs with up to 90% discount: regular tasks (shown below) or managed jobs (shown in `benchmark`).

As a regular task, a preempted spot instance doesn't recover. It's still often worth it. Save results, checkpoints or data in the bucket folder `/r2` to protect against random termination.

Let's declare a Hugging Face repository with a bigger model:
```bash
MODEL=Qwen/Qwen2.5-Coder-32B-Instruct
VERSION=b47205940b83b5b484577359f71ee7b88472df67
```
Notice we added `--use-spot` to `sky launch`. We request accelerators with `--gpus` outside the template to make it obvious that `-tp`, short for `--tensor-parallel-size`, must split tensors across 4 GPUs. This option is passed to `vllm serve`. 

At the time of writing, 3 regions offer this spot configuration for less than $1/hour, instead of $5 to $6 on demand. Look up SkyPilot catalog in `~/.sky/catalogs/v*/aws/vms.csv`, identify these regions and request [quotas](/mesh/README.md#quotas) for them.
```bash
(lmrun-py3.11) workspace % sky launch vllm.yaml -c vllm --gpus L4:4 --use-spot \
    --env MODEL=$MODEL --env VERSION=$VERSION --env SERVE_OPTS="-tp 4"
Task from YAML spec: vllm.yaml
Considered resources (1 node):
----------------------------------------------------------------------------------------------------
 CLOUD   INSTANCE            vCPUs   Mem(GB)   ACCELERATORS   REGION/ZONE       COST ($)   CHOSEN
----------------------------------------------------------------------------------------------------
 AWS     g6.12xlarge[Spot]   48      192       L4:4           ap-northeast-2a   0.66          ✔
----------------------------------------------------------------------------------------------------
```
SkyPilot found 4 x L4s on a spot VM in Seoul for less than the price of a single on-demand GPU.

Once you redirected the port `8000` through SSH like above, specify the Hugging Face id as the model of your request:
```
curl http://localhost:8000/v1/chat/completions -H "Content-Type: application/json" -d '{
  "model": "Qwen/Qwen2.5-Coder-32B-Instruct",
  "messages": [
    {"role": "system", "content": "You are a helpful code assistant."},
    {"role": "user", "content": "Can you keep coding while I grab a coffee?"}
  ]
}'
```

### Sustained Throughput: private model or dataset
To expose large and private model weights or datasets, consider Hugging Face repos or a bucket on Oracle Cloud. According to current pricing, they should deliver sustained throughput (contrary to R2) and cost-effective distribution of data to any infrastructure provider over the internet. We demonstrate HF below. An OCI bucket would be mounted within templates like R2.

*Prerequisites*: 
- Cudo Compute [configuration](https://docs.skypilot.co/en/latest/getting-started/installation.html#cudo-compute) to automatically push a model to a private HF repo. Besides GPUs, Cudo is handy for CPU workloads like data preparation without egress fees (afaik). A mere 32B model upload costs more than $5 in network outbound fees on all 3 hyperscalers. Check that Cudo is enabled with `sky check`.
- Set a public SSH key on [HF](https://huggingface.co/settings/keys).
- Create a new private repo by visiting [huggingface.co/new](huggingface.co/new). Name it `Qwen2.5-Coder-32B-Instruct` for this example.

1. upload public model to private Hugging Face repository for testing 
```bash
sky launch hf-to-private.yaml -i 5 --down \
    --env ORG=Qwen --env NAME=Qwen2.5-Coder-32B-Instruct \
    --env NEW_ORG="<YOUR_HF_USERNAME>" --env SSH_KEY="</path/to/hf/private/key>"
```

## Cloudflare R2 storage
If you're already familiar with S3, R2 is a more efficient substitute for LMRun global architecture, even when compute is provided by AWS.

1. For access to data or models on object storage, you will need a Cloudflare account with a payment method for R2, which won't be used within the free tier.
2. On Cloudflare, go to “R2 Object Storage” in the left-side menu > “Create bucket” > Call it “lmrun” and click “Create bucket”.
3. Configure R2 as described in SkyPilot [doc](https://docs.skypilot.co/en/latest/getting-started/installation.html#cloudflare-r2). When creating the API token, restrict permissions to "Object Read & Write" and apply to the `lmrun` bucket only. Note that all values you need, incl. the Cloudflare Account ID, are on the final screen. The account is the first part of the URL in `https://<Your Account ID>.r2.cloudflarestorage.com`.
4. Check your configuration with `sky check`: the command should output "Cloudflare (for R2 object store): enabled" in green.