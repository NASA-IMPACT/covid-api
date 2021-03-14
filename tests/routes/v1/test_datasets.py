"""Test /v1/datasets endpoints"""


import json
from unittest.mock import patch

import boto3
import botocore
from moto import mock_s3

from covid_api.core.config import INDICATOR_BUCKET

DATASET_METADATA_FILENAME = "dev-dataset-metadata.json"
DATASET_METADATA_GENERATOR_FUNCTION_NAME = "dev-dataset-metadata-generator"

@mock_s3
def _setup_s3(empty=False):
    s3 = boto3.resource("s3")
    bucket = s3.Bucket(INDICATOR_BUCKET)
    bucket.create()
    if empty:
        return bucket
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
        bucket.put_object(Body=content, Key=key)
    return bucket


@mock_s3
def test_metadata_file_generation_triggered_if_not_found(
    app, dataset_manager, monkeypatch
):

    _setup_s3(empty=True)

    with patch("covid_api.db.static.datasets.invoke_lambda") as mocked_invoke_lambda:

        mocked_invoke_lambda.return_value = {"result": "success"}
        # Load dataset will invoke the mocked-lambda and then attempt to load the file
        # from S3 once the lambda finished executing. Since the mocked lambda
        # doesn't actually write anything to S3 in this test, the call to load the file
        # from S3 will fail. This is not a problem since this test is just to ascertain
        # that the lambda was in fact triggered.
        try:
            dataset_manager()._load_remote_metadata()
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "404":
                pass

        mocked_invoke_lambda.assert_called_with(
            lambda_function_name=DATASET_METADATA_GENERATOR_FUNCTION_NAME
        )


@mock_s3
def test_datasets(app):
    _setup_s3()
    response = app.get("v1/datasets")

    assert response.status_code == 200
    content = json.loads(response.content)

    assert "co2" in [d["id"] for d in content["datasets"]]
    assert "detections-plane" in [d["id"] for d in content["datasets"]]


@mock_s3
def test_spotlight_datasets(app):
    _setup_s3()
    response = app.get("v1/datasets/tk")

    assert response.status_code == 200

    content = json.loads(response.content)
    assert "co2" in [d["id"] for d in content["datasets"]]
    assert "detections-plane" in [d["id"] for d in content["datasets"]]
    assert "detections-ship" not in [d["id"] for d in content["datasets"]]


@mock_s3
def test_incorrect_dataset_id(app):
    _setup_s3()

    response = app.get("/v1/datasets/NOT_A_VALID_DATASET")
    assert response.status_code == 404
