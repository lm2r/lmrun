# LMRun

Multi-cloud AI environment built on [SkyPilot](https://github.com/skypilot-org/skypilot)

- Turns multiple cloud accounts into an integrated AI platform
- Provides on-demand GPUs with a seamless DX through SkyPilot

> E.g. LMRun connects isolated clusters and MLOps servers in one bootstrap command

LMRun is a distribution: it has already made infrastructure choices to include a cloud setup, networking and services, that run below, across and on top of SkyPilot. 

*features*
- Global VPN network of GPUs for secure availability and cheaper compute
- Open stack: work with any tool or framework on cloud-agnostic infrastructure
- No data lock-in: free or low-cost egress bandwidth for high throughput
- Hyperscaler (AWS) extension to outsource AI compute

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

