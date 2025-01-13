#!/usr/bin/env bash

conda init bash
# create the last supported environment, Python 3.12, to install vLLM
conda create -n vllm python=3.12 -y
conda activate vllm
pip install vllm

