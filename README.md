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
1. Set up your [local environment](#local-environment).
2. Follow instructions in `init` to initialize the cloud environment.
3. Follow instructions in `mesh` to deploy the cluster mesh.
4. Go to `workspace` for example templates and use cases. 
5. Make them yours: change models, tune configuration, add resources, etc..

## Local Environment
1. Complete [system configuration](#system-configuration).
2. Set the last Python version compatible with SkyPilot `poetry env use ~/.pyenv/versions/3.11.*/bin/python` (previously installed in System Configuration).
3. Optional: if your IDE automatically loads virtual environments like VSCode within projects, run `poetry config virtualenvs.in-project true` so it works out of the box.
4. Create the local environment: `poetry install --with dev`.
5. Activate it: `poetry shell`.

## System Configuration
These steps prepare the local system to run the environment. We provide guidance *from scratch*.
1. A global installation of [Poetry](https://python-poetry.org) is expected. We recommend to first install [pipx](https://pipx.pypa.io/stable/) to isolate global packages from the OS and then run `pipx install poetry`.
2. Configuration reads a `.env` file and requires a plugin to load it automatically: `poetry self add poetry-plugin-dotenv`.
3. Install Python 3.11 if it isn't available locally. You can use [Pyenv](https://github.com/pyenv/pyenv?tab=readme-ov-file#installation): `pyenv install 3.11`.
4. Install [Pulumi](https://www.pulumi.com/docs/install/) to manage cloud resources.
5. Use AWS CLI V2 to create an `lmrun` [profile](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html#cli-configure-files-methods) with admin permissions. We recommend creating a new AWS account for this profile. If you already have a main account, create the new account from AWS [Organizations](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_introduction.html). To use another profile name, edit `AWS_PROFILE` in `.env`.

