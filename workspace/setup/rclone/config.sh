#!/usr/bin/env bash

DIR=~/.config/rclone
CONF=$DIR/rclone.conf
R2_DOMAIN=r2.cloudflarestorage.com

mkdir -p $DIR

cat ~/.cloudflare/r2.credentials | sed 's/aws_//' >> $CONF
# 'no_check_bucket = true' required with object-level permissions
printf "type = s3\nprovider = Cloudflare\nno_check_bucket = true\n" >> $CONF
echo "endpoint = https://`cat ~/.cloudflare/accountid`.$R2_DOMAIN" >> $CONF
