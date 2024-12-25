"""User-defined values treated as stack inputs"""

# the network spans all regions where at least one of these instances is available
VM_AWS = [
    "g6.xlarge",  # 1 x L4 GPU: 24 GB, 4 vCPUs, 16 GiB
    "g6.2xlarge",  # 1 x L4 GPU: 24 GB, 8 vCPUs, 32 GiB
    "g6.12xlarge",  # 4 x L4 GPU: 96 GB, 48 vCPUs, 192 GiB
]

# name of resources like VPCs, SGs or IAM role targeted by SkyPilot
SKY_REF = "lmrun"  # referenced in sky/config.yaml
