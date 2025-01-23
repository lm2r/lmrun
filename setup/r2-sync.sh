#!/usr/bin/env bash
# upload local setup scripts to R2 bucket

 cf_account=`cat ~/.cloudflare/accountid`
 export AWS_ENDPOINT_URL=https://$cf_account.r2.cloudflarestorage.com
 export AWS_SHARED_CREDENTIALS_FILE=~/.cloudflare/r2.credentials
 export AWS_PROFILE=r2

git_root=`git rev-parse --show-toplevel`
aws s3 sync $git_root/setup s3://lmrun/setup \
    --exclude "r2-sync.sh*" \
    --exclude "test_*" \
    --exclude "*.pyc"
