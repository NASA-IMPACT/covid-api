"""Test /v1/datasets endpoints"""


import json
from unittest.mock import patch

from stack.config import DATASET_METADATA_GENERATOR_FUNCTION_NAME


def test_metadata_file_generation_triggered_if_not_found(
    app, lambda_function, empty_bucket, dataset_manager, monkeypatch
):
    with patch("covid_api.db.static.datasets.invoke_lambda") as mocked_invoke_lambda:

        mocked_invoke_lambda.return_value = {"result": "success"}
        dataset_manager._load_domain_metadata()

        mocked_invoke_lambda.assert_called_with(
            lambda_function_name=DATASET_METADATA_GENERATOR_FUNCTION_NAME
        )


def test_datasets(app, bucket):
    response = app.get("v1/datasets")
    assert response.status_code == 200
    content = json.loads(response.content)
    assert "co2" in [d["id"] for d in content["datasets"]]
    assert "detections-plane" in [d["id"] for d in content["datasets"]]


def test_spotlight_datasets(app, bucket):
    response = app.get("v1/datasets/tk")
    assert response.status_code == 200
    content = json.loads(response.content)
    assert "co2" in [d["id"] for d in content["datasets"]]
    assert "detections-plane" in [d["id"] for d in content["datasets"]]
    assert "detections-ship" not in [d["id"] for d in content["datasets"]]


def test_incorrect_dataset_id(app, bucket):
    response = app.get("/v1/datasets/NOT_A_VALID_DATASET")
    assert response.status_code == 404
