#!/usr/bin/env bash

conda create -n vllm python=3.12 -y
conda activate vllm
# in vLLM, hf-transfer requires no environment variable if available
# https://github.com/vllm-project/vllm/pull/3817
pip install vllm hf-transfer