# Cluster Mesh
The cluster mesh is a global network of peered VPCs that leverages sky compute across regions without losing the ability to gather metadata: trace prompts, scale experiments and track costs in central services. 

It enables service discovery and removes the need to expose public ports or manually configure addresses and credentials for each tool, on every VM.

## Configuration
### SkyPilot
Copy `sky/config.yaml` to `~/.sky/config.yaml`.

### Instance Types
VPCs are only deployed in regions where selected accelerators are available. They are defined by instance types in `Pulumi.yaml`. 

1. Edit the `vmAws` list to include all supported types in the cluster.
2. Update the Pulumi stack following the deployment process below everytime `Pulumi.yaml` is edited.

## Deployment
Prerequisite: first 2 steps of the [Quickstart](/README.md#quickstart)
1. `poetry shell` to activate the environment
2. log in to Pulumi admin backend: first, export your account ID or retrieve it like below
```bash
export AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
pulumi login s3://pulumi-admin-$AWS_ACCOUNT
```
3. Optional: initialize the stack if you don't already have a local `Pulumi.lmrun.yaml` in this folder. It should contain an `encryptedKey` field. Run `pulumi stack init lmrun --secrets-provider awskms://alias/pulumi/admin` if the stack has never been deployed or `pulumi config refresh` otherwise.
4. `pulumi up`
5. Deal with instance quotas over time. See section below.

### Quotas
By default, cloud accounts have restricted access to AI accelerators. You need to request them across all regions but automation doesn't help. Most requests will be disregarded if many are created at once.
- SkyPilot documents the [process](https://docs.skypilot.co/en/latest/cloud-setup/quota.html#aws): note that the quota value isn't the number of instances but the "max total number of vCPUs for all VMs of an instance type in a region".
- We recommend to monitor the logs of `sky launch`. When such messages occur, request quota increases in the region logged above.
> create_instances: Attempt failed with An error occurred (VcpuLimitExceeded) when calling the RunInstances operation

This dictionary shows codes and names of common minimum quotas to run default LMRun templates:
```python
QUOTAS_AWS = {
    # "Running On-Demand G and VT instances"
    "L-DB2E81BA": 8,
    # "All G and VT Spot Instance Requests"
    "L-3819A6DF": 48,
}
```

### New AWS Regions
LMRun assigns a network range to at least 30 regions. To add a new one that AWS may have just launched:
1. Add an entry at the bottom of the CIDR block allocation in `aws/network/cidr_blocks.py`.
2. Most likely, the new region will be available by opting-in. To keep a consistent state, we recommend activating it by running `pulumi up` in `init`, which will automatically fetch all regions before applying the update.

New regions may have accelerators available before all resources are supported via Cloud Control API, i.e. they're not production-ready, yet. If the deployment fails for this reason, add the offending region to `ROGUE_REGIONS` in `aws/region/selection.py`.

