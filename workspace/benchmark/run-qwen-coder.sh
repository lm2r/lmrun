#!/usr/bin/env bash

export MODEL=Qwen/Qwen2.5-Coder-32B-Instruct
export VERSION=b47205940b83b5b484577359f71ee7b88472df67

sky launch model-server.yaml --env MODEL --env VERSION -c qwen-coder 
