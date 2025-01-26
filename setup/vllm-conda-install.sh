#!/usr/bin/env bash

conda init bash
# create the last supported environment, Python 3.12, to install vLLM
conda create -n vllm python=3.12 -y
conda activate vllm
# in vllm, hf-transfer requires no environment variable if available
# https://github.com/vllm-project/vllm/pull/3817
pip install vllm hf-transfer