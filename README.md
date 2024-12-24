# LMRun

Infrastructure as Code (IaC) for AI practitioners
- Turn your cloud accounts into an AI platform
- Ensure the cheap availability of AI accelerators with a seamless DX

[SkyPilot](https://github.com/skypilot-org/skypilot) made these **features** possible
- Global network for better availability and cheaper compute
- Open stack: work with any tool or framework, LMRun runs underneath
- No data lock-in: free bandwidth thanks to [R2](https://www.cloudflare.com/developer-platform/products/r2/)
- Deploy on hyperscalers for enterprise-grade integrations and services

> LMRun is a great fit when managed services are not

## Quickstart
1. Set up your [local environment](#local-environment).
2. Follow instructions in `cloud_init` to initialize the cloud environment.
3. Follow instructions in `cluster_mesh` to deploy the cluster mesh.
4. Pick any other root subfolder to launch a use case or `workspace_compute` if you're new to LMRun. 
5. Make it yours: change models, tune configuration, add resources, etc..

## Local Environment
1. Complete [system configuration](#system-configuration).
2. Set the last Python version compatible with SkyPilot `poetry env use ~/.pyenv/versions/3.11.*/bin/python` (previously installed in System Configuration).
3. Create the local environment: `poetry install --with dev`.
4. Activate it: `poetry shell`.

## System Configuration
These steps prepare the local system to run the environment. We provide guidance *from scratch*.
1. A global installation of [Poetry](https://python-poetry.org) is expected. We recommend to first install [pipx](https://pipx.pypa.io/stable/) to isolate global packages from the OS and then run `pipx install poetry`.
2. Configuration reads a `.env` file and requires a plugin to load it automatically: `poetry self add poetry-plugin-dotenv`.
3. Install Python 3.11 if it isn't available locally. You can use [Pyenv](https://github.com/pyenv/pyenv?tab=readme-ov-file#installation): `pyenv install 3.11`.
4. Install [Pulumi](https://www.pulumi.com/docs/install/) to manage cloud resources.
5. Create an `lmrun` AWS [profile](https://docs.aws.amazon.com/cli/v1/userguide/cli-configure-files.html) with admin permissions in `~/.aws/credentials`. We recommend creating a new AWS account for this profile. If you already have a main account, create the new account from AWS [Organizations](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_introduction.html). To use another profile name, edit `AWS_PROFILE` in `.env`.
