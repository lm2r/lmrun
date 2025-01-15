#!/usr/bin/env bash

export MODEL=NovaSky-AI/Sky-T1-32B-Preview
export VERSION=1e3f4c62a30c7ce70f4b3a3b952895d866943551

sky launch model-server.yaml --env MODEL --env VERSION -c sky-t1
