"""Test /v1/datasets endpoints"""

import boto3
import json
from datetime import datetime
from moto import mock_s3
from covid_api.core.config import INDICATOR_BUCKET


@mock_s3
def _setup_s3():
    s3 = boto3.client("s3")
    s3.create_bucket(Bucket=INDICATOR_BUCKET)

    s3_keys = [
        "xco2/GOSAT_XCO2_201901_be_BG_circle_cog.tif",
        "xco2/GOSAT_XCO2_201904_be_BG_circle_cog.tif",
        "xco2/GOSAT_XCO2_201906_be_BG_circle_cog.tif",
        "oc3_chla_anomaly/anomaly-chl-tk-2020_01_29.tif",
        "oc3_chla_anomaly/anomaly-chl-tk-2020_02_05.tif",
        "oc3_chla_anomaly/anomaly-chl-tk-2020_03_02.tif",
        "BM_500M_DAILY/VNP46A2_V011_Beijing_2020_01_01_cog.tif",
        "BM_500M_DAILY/VNP46A2_V011_Beijing_2020_02_29_cog.tif",
        "BM_500M_DAILY/VNP46A2_V011_Beijing_2020_03_20_cog.tif",
        "indicators/test/super.csv",
    ]
    for key in s3_keys:
        s3.put_object(
            Bucket=INDICATOR_BUCKET, Key=key, Body=b"test",
        )

    return s3


@mock_s3
def test_databases(app):

    _setup_s3()

    response = app.get("/v1/datasets")

    assert response.status_code == 200

    content = json.loads(response.content)
    assert "datasets" in content
    assert len(content["datasets"]) > 0


@mock_s3
def test_datasets_monthly(app):

    _setup_s3()

    response = app.get("/v1/datasets/be")
    assert response.status_code == 200

    content = json.loads(response.content)
    assert "datasets" in content

    dataset_info = [d for d in content["datasets"] if d["id"] == "co2"][0]
    assert dataset_info["domain"][0] == datetime.strftime(
        datetime(2019, 1, 1), "%Y-%m-%dT%H:%M:%S"
    )
    assert dataset_info["domain"][1] == datetime.strftime(
        datetime(2019, 6, 1), "%Y-%m-%dT%H:%M:%S"
    )


@mock_s3
def test_datasets_daily(app):
    """test /datasets endpoint"""

    # aws mocked resources
    _setup_s3()

    response = app.get("/v1/datasets/tk")
    assert response.status_code == 200

    content = json.loads(response.content)
    assert "datasets" in content

    dataset_info = [d for d in content["datasets"] if d["id"] == "water-chlorophyll"][0]
    assert dataset_info["domain"][0] == datetime.strftime(
        datetime(2020, 1, 29), "%Y-%m-%dT%H:%M:%S"
    )
    assert dataset_info["domain"][1] == datetime.strftime(
        datetime(2020, 3, 2), "%Y-%m-%dT%H:%M:%S"
    )


@mock_s3
def test_datasets_spotlight_label(app):
    """test /datasets endpoint"""

    # aws mocked resources
    _setup_s3()

    response = app.get("/v1/datasets/be")
    assert response.status_code == 200

    content = json.loads(response.content)
    assert "datasets" in content

    dataset_info = [d for d in content["datasets"] if d["id"] == "nightlights-viirs"][0]
    assert dataset_info["domain"][0] == datetime.strftime(
        datetime(2020, 1, 1), "%Y-%m-%dT%H:%M:%S"
    )
    assert dataset_info["domain"][1] == datetime.strftime(
        datetime(2020, 3, 20), "%Y-%m-%dT%H:%M:%S"
    )


@mock_s3
def test_incorrect_dataset_id(app):
    response = app.get("/v1/datasets/NOT_A_VALID_DATASET")
    assert response.status_code == 404
