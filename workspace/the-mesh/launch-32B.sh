#!/usr/bin/env bash
set -eu

model_name=$1
task=${2:-model-server.yaml}
export MODEL=${3:-Qwen/Qwen2.5-Coder-32B-Instruct}
export VERSION=${4:-b47205940b83b5b484577359f71ee7b88472df67}

# execute `sky jobs launch` instead of `sky launch` when the task ends with job.yaml
if [[ $task == *job.yaml ]]; then
    subcommand=jobs
else
    subcommand=""
fi
sky $subcommand launch $task --env MODEL --env VERSION -c $model_name 