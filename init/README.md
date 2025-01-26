# Cloud Initialization

This Pulumi stack creates the bare minimum resources to manage cloud deployments.

### Resources
- Pulumi admin + app state buckets: permissive management in admin is isolated from the app backend, intended for least privilege roles, e.g. CI
- respective encryption keys for sensitive values stored in admin and app backends
- activation of AWS regions where opt-in is required 

This stack produces a local Pulumi state in `aws/.pulumi`, resulting from `pulumi` commands. It isn't too critical as it's easy enough to keep track of two keys and two buckets. After this bootstrap, resources will be tracked in remote backends.

## Usage
*Prerequisite*: the local environment must have been configured (see main README).
1. Activate the environment: `. ../.venv/bin/activate` from this folder
2. Head to a provider folder, e.g. `cd aws`
3. Provision resources with `pulumi up -s $AWS_PROFILE` to reuse the profile as a stack name matching the environment

