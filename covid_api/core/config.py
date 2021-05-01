"""Config."""

import os

import yaml

config_object = yaml.load(
    open(f"{os.path.abspath('.')}/stack/config.yml", "r"), Loader=yaml.FullLoader
)

STAGE = os.environ.get("STAGE", config_object["STAGE"])
API_VERSION_STR = "/v1"

PROJECT_NAME = config_object["PROJECT_NAME"]

SERVER_NAME = os.getenv("SERVER_NAME")
SERVER_HOST = os.getenv("SERVER_HOST")
BACKEND_CORS_ORIGINS = os.getenv(
    "BACKEND_CORS_ORIGINS", default="*"
)  # a string of origins separated by commas, e.g: "http://localhost, http://localhost:4200, http://localhost:3000, http://localhost:8080, http://local.dockertoolbox.tiangolo.com"

DISABLE_CACHE = os.getenv("DISABLE_CACHE")
MEMCACHE_HOST = os.environ.get("MEMCACHE_HOST")
MEMCACHE_PORT = int(os.environ.get("MEMCACHE_PORT", 11211))
MEMCACHE_USERNAME = os.environ.get("MEMCACHE_USERNAME")
MEMCACHE_PASSWORD = os.environ.get("MEMCACHE_PASSWORD")

INDICATOR_BUCKET = os.environ.get("INDICATOR_BUCKET", config_object["INDICATOR_BUCKET"])

DATASET_METADATA_FILENAME = os.environ.get(
    "DATASET_METADATA_FILENAME", config_object["DATASET_METADATA_FILENAME"]
)

DATASET_METADATA_GENERATOR_FUNCTION_NAME = os.environ.get(
    "DATASET_METADATA_GENERATOR_FUNCTION_NAME", "dev-dataset-metadata-generator"
)

DT_FORMAT = "%Y-%m-%d"
MT_FORMAT = "%Y%m"
