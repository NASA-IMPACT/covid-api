"""``pytest`` configuration."""

import io
import json
import os
import zipfile

import boto3
import pytest
import rasterio
from botocore.exceptions import ClientError
from moto import mock_iam, mock_lambda, mock_s3
from rasterio.io import DatasetReader

from covid_api.core.config import INDICATOR_BUCKET
from stack.config import (
    DATASET_METADATA_FILENAME,
    DATASET_METADATA_GENERATOR_FUNCTION_NAME,
)

from starlette.testclient import TestClient


@pytest.fixture(autouse=True)
def aws_credentials(monkeypatch):
    monkeypatch.setenv("DISABLE_CACHE", "YESPLEASE")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "jqt")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "rde")


@pytest.fixture
def app(aws_credentials) -> TestClient:
    """Make sure we use monkeypatch env."""

    from covid_api.main import app

    return TestClient(app)


def mock_rio(src_path: str) -> DatasetReader:
    """Mock rasterio.open."""
    prefix = os.path.join(os.path.dirname(__file__), "fixtures")
    assert src_path.startswith("https://myurl.com/")
    return rasterio.open(os.path.join(prefix, "cog.tif"))


@pytest.fixture
def lambda_iam_role(aws_credentials):
    with mock_iam():
        iam = boto3.client("iam", region_name="us-east-1")
        try:
            yield iam.get_role(RoleName="my-role")["Role"]["Arn"]
        except ClientError:
            yield iam.create_role(
                RoleName="my-role",
                AssumeRolePolicyDocument="some policy",
                Path="/my-path/",
            )["Role"]["Arn"]


@pytest.fixture
def lambda_client(aws_credentials):
    """Yields a mocked boto3 s3 client"""
    with mock_lambda():
        yield boto3.client("lambda", region_name="us-east-1")


@pytest.fixture
def s3(aws_credentials):
    """Yields a mocked boto3 s3 client"""
    with mock_s3():
        yield boto3.client("s3", region_name="us-east-1")


@pytest.fixture
def empty_bucket(s3):
    """Yields an empty mocked s3 bucket"""
    bucket = s3.create_bucket(Bucket=INDICATOR_BUCKET)
    return bucket


@pytest.fixture
def bucket(s3, empty_bucket):
    """Yields a bucket pre-populated with empty files to parse for date
    domain extraction"""
    s3_keys = [
        ("indicators/test/super.csv", b"test"),
        (
            DATASET_METADATA_FILENAME,
            json.dumps(
                {
                    "_all": {
                        "co2": {
                            "domain": ["2019-01-01T00:00:00Z", "2020-01-01T00:00:00Z"]
                        },
                        "detections-plane": {
                            "domain": [
                                "2019-01-01T00:00:00Z",
                                "2019-10-10T00:00:00Z",
                                "2020-01-01T:00:00:00Z",
                            ]
                        },
                    },
                    "global": {
                        "co2": {
                            "domain": ["2019-01-01T00:00:00Z", "2020-01-01T00:00:00Z"]
                        }
                    },
                    "tk": {
                        "detections-plane": {
                            "domain": [
                                "2019-01-01T00:00:00Z",
                                "2019-10-10T00:00:00Z",
                                "2020-01-01T:00:00:00Z",
                            ]
                        }
                    },
                    "ny": {
                        "detections-ship": {
                            "domain": [
                                "2019-01-01T00:00:00Z",
                                "2019-10-10T00:00:00Z",
                                "2020-01-01T:00:00:00Z",
                            ]
                        }
                    },
                }
            ),
        ),
    ]
    for key, content in s3_keys:
        s3.put_object(
            Bucket=INDICATOR_BUCKET, Key=key, Body=content,
        )
    return empty_bucket


@pytest.fixture
def lambda_zip_file():
    func_str = """
import boto3
def lambda_handler(event, context):
    result = {"result": "success"}
    if event.get("fail"):
        raise Exception
    if event:
        result.update(event)
    return result
"""
    zip_output = io.BytesIO()
    zip_file = zipfile.ZipFile(zip_output, "w", zipfile.ZIP_DEFLATED)
    zip_file.writestr("lambda_function.py", func_str)
    zip_file.close()
    zip_output.seek(0)
    return zip_output.read()


@pytest.fixture
def lambda_function(lambda_client, lambda_iam_role, lambda_zip_file):
    function = lambda_client.create_function(
        FunctionName=DATASET_METADATA_GENERATOR_FUNCTION_NAME,
        Runtime="python3.8",
        Role=lambda_iam_role,
        Handler="lambda_function.lambda_handler",
        Code={"ZipFile": lambda_zip_file},
        Description="Test Lambda Function",
        Timeout=3,
        MemorySize=128,
        Publish=True,
    )
    return function


@pytest.fixture
def db_utils(aws_credentials):

    from covid_api.db import utils

    return utils


@pytest.fixture
def dataset_manager(aws_credentials):
    from covid_api.db.static.datasets import DatasetManager

    return DatasetManager()
