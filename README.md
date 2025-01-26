# LMRun

AI workload platform as a SkyPilot distribution incl. cloud infra, networking & services
- Turn your cloud accounts into an AI platform
- Ensure the cheap availability of AI accelerators with a seamless DX

[SkyPilot](https://github.com/skypilot-org/skypilot) made these *features* possible
- Global network of multiple clouds for better availability and cheaper compute
- Open stack: work with any tool or framework on cloud-agnostic infrastructure
- No data lock-in: free or low-cost egress bandwidth for high throughput
- Expand hyperscaler accounts (AWS) to outsource AI compute

> LMRun integrates SkyPilot clusters and multiple clouds into a single environment.

## Quickstart
1. Set up your [local environment](#local-environment)
2. Follow instructions in `init` to initialize the cloud environment
3. Follow instructions in `mesh` to deploy the cluster mesh
4. Go to `workspace` for example templates and use cases
5. Make them yours: change models, tune configuration, add resources, etc

## Local Environment
*Prerequisite*: if necessary, install [system dependencies](#system-dependencies). At the very least, you need to configure an AWS profile.

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/)
2. Run `uv sync --extra dev` in this directory to create the virtual environment and install all dependencies
3. Set the export of variables when activating the environment
```bash
echo 'set -a; source "$VIRTUAL_ENV/../.env"; set +a' >> .venv/bin/activate
```
4. Activate the environment: `source .venv/bin/activate`

## System Dependencies
1. Install [Pulumi](https://www.pulumi.com/docs/install/) to manage cloud resources
2. Use AWS CLI V2 to create an `lmrun` profile with admin permissions: `aws configure --profile lmrun`. We recommend creating a new AWS account for this profile. If you already have a main account, create the new account from AWS [Organizations](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_introduction.html). To use another profile name, edit `AWS_PROFILE` in `.env`.

