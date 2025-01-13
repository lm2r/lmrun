#!/usr/bin/env bash

# this script must run as the sky user to locate credentials
if [ "$(whoami)" = "root" ]; then
    echo "This script must NOT be run as root" >&2
    exit 1
fi

DIR=~/.config/rclone
CONF=$DIR/rclone.conf
R2_DOMAIN=r2.cloudflarestorage.com

mkdir -p $DIR

cat ~/.cloudflare/r2.credentials | sed 's/aws_//' >> $CONF
# 'no_check_bucket = true' required with object-level permissions
printf "type = s3\nprovider = Cloudflare\nno_check_bucket = true\n" >> $CONF
echo "endpoint = https://`cat ~/.cloudflare/accountid`.$R2_DOMAIN" >> $CONF
