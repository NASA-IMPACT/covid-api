"""STACK Configs."""

import os
import yaml

config = yaml.load(open('stack/config.yml', 'r'), Loader=yaml.FullLoader)

PROJECT_NAME = config['PROJECT_NAME']
STAGE = config.get('STAGE') or 'dev'

# primary bucket
BUCKET = config['BUCKET']

# Additional environement variable to set in the task/lambda
TASK_ENV: dict = dict()

# Existing VPC to point ECS/LAMBDA stacks towards. Defaults to creating a new
# VPC if no ID is supplied.
VPC_ID = os.environ.get("VPC_ID") or config['VPC_ID']


################################################################################
#                                                                              #
#                                   ECS                                        #
#                                                                              #
################################################################################
# Min/Max Number of ECS images
MIN_ECS_INSTANCES: int = config['MAX_ECS_INSTANCES']
MAX_ECS_INSTANCES: int = config['MAX_ECS_INSTANCES']

# CPU value      |   Memory value
# 256 (.25 vCPU) | 0.5 GB, 1 GB, 2 GB
# 512 (.5 vCPU)  | 1 GB, 2 GB, 3 GB, 4 GB
# 1024 (1 vCPU)  | 2 GB, 3 GB, 4 GB, 5 GB, 6 GB, 7 GB, 8 GB
# 2048 (2 vCPU)  | Between 4 GB and 16 GB in 1-GB increments
# 4096 (4 vCPU)  | Between 8 GB and 30 GB in 1-GB increments
TASK_CPU: int = config['TASK_CPU']
TASK_MEMORY: int = config['TASK_MEMORY']

################################################################################
#                                                                              #
#                                 LAMBDA                                       #
#                                                                              #
################################################################################
TIMEOUT: int = config['TIMEOUT']
MEMORY: int = config['MEMORY']

# stack skips setting concurrency if this value is 0
# the stack will instead use unreserved lambda concurrency
MAX_CONCURRENT: int = 500 if STAGE == "prod" else config['MAX_CONCURRENT']

# Cache
CACHE_NODE_TYPE = config['CACHE_NODE_TYPE']
CACHE_ENGINE = config['CACHE_ENGINE']
CACHE_NODE_NUM = config['CACHE_NODE_NUM']
