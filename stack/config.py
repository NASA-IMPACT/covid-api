"""STACK Configs."""

import os

PROJECT_NAME = "covid-api"
STAGE = os.environ.get("STAGE", "dev")

# primary bucket
BUCKET = "covid-eo-data"

# Additional environement variable to set in the task/lambda
TASK_ENV: dict = dict()

# Existing VPC to point ECS/LAMBDA stacks towards. Defaults to creating a new
# VPC if no ID is supplied.
VPC_ID = os.environ.get("VPC_ID")


################################################################################
#                                                                              #
#                                   ECS                                        #
#                                                                              #
################################################################################
# Min/Max Number of ECS images
MIN_ECS_INSTANCES: int = 5
MAX_ECS_INSTANCES: int = 50

# CPU value      |   Memory value
# 256 (.25 vCPU) | 0.5 GB, 1 GB, 2 GB
# 512 (.5 vCPU)  | 1 GB, 2 GB, 3 GB, 4 GB
# 1024 (1 vCPU)  | 2 GB, 3 GB, 4 GB, 5 GB, 6 GB, 7 GB, 8 GB
# 2048 (2 vCPU)  | Between 4 GB and 16 GB in 1-GB increments
# 4096 (4 vCPU)  | Between 8 GB and 30 GB in 1-GB increments
TASK_CPU: int = 256
TASK_MEMORY: int = 512

################################################################################
#                                                                              #
#                                 LAMBDA                                       #
#                                                                              #
################################################################################
TIMEOUT: int = 10
MEMORY: int = 1536

# stack skips setting concurrency if this value is 0
# the stack will instead use unreserved lambda concurrency
MAX_CONCURRENT: int = 500 if STAGE == "prod" else 0

# Cache
CACHE_NODE_TYPE = "cache.m5.large"
CACHE_ENGINE = "memcached"
CACHE_NODE_NUM = 1
