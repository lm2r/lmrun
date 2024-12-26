# Continuous Integration

This stack provisions an OIDC provider for GitHub in AWS to let tests interact with a cloud environment in CI.

> Always check the policy which is about to be updated in `__main__.py`, in case a permissive privilege has been unintentionally merged.

Any public branch is granted these permissions (can be modified in the trust policy). GitHub default settings still require permission before new contributors can run workflows.

## Launch
1. `export GITHUB_TOKEN=...` with a token from the GitHub account (username or organization) where to set up CI
2. `export GITHUB_OWNER=...` with the GitHub account name (would be `lm2r` for the original repo)
2. log in to Pulumi admin backend
```bash
export AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
pulumi login s3://pulumi-admin-$AWS_ACCOUNT
```
3. initialize `pulumi stack init lmrun --secrets-provider awskms://alias/pulumi/admin` or refresh the stack config `pulumi config refresh` if it isn't available locally
4. `pulumi up`
