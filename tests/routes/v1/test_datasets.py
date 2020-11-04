"""Test /v1/datasets endpoints"""

import json
from datetime import datetime

import boto3
from moto import mock_s3

from covid_api.core.config import INDICATOR_BUCKET


@mock_s3
def _setup_s3(empty=False):
    s3 = boto3.client("s3")
    s3.create_bucket(Bucket=INDICATOR_BUCKET)

    if empty:
        return s3

    s3_keys = [
        "xco2-mean/GOSAT_XCO2_201901_be_BG_circle_cog.tif",
        "xco2-mean/GOSAT_XCO2_201904_be_BG_circle_cog.tif",
        "xco2-mean/GOSAT_XCO2_201906_be_BG_circle_cog.tif",
        "oc3_chla_anomaly/anomaly-chl-tk-2020_01_29.tif",
        "oc3_chla_anomaly/anomaly-chl-tk-2020_02_05.tif",
        "oc3_chla_anomaly/anomaly-chl-tk-2020_03_02.tif",
        "bm_500m_daily/VNP46A2_V011_be_2020_01_01_cog.tif",
        "bm_500m_daily/VNP46A2_V011_be_2020_02_29_cog.tif",
        "bm_500m_daily/VNP46A2_V011_be_2020_03_20_cog.tif",
        "bm_500m_daily/VNP46A2_V011_EUPorts_2020_01_01_cog.tif",
        "bm_500m_daily/VNP46A2_V011_EUPorts_2020_02_29_cog.tif",
        "bm_500m_daily/VNP46A2_V011_EUPorts_2020_03_20_cog.tif",
        "bmhd_30m_monthly/BMHD_VNP46A2_du_202005_cog.tif",
        "bmhd_30m_monthly/BMHD_VNP46A2_du_202006_cog.tif",
        "bmhd_30m_monthly/BMHD_VNP46A2_du_202007_cog.tif",
        "OMNO2d_HRM/OMI_trno2_0.10x0.10_200401_Col3_V4.nc.tif",
        "OMNO2d_HRM/OMI_trno2_0.10x0.10_200708_Col3_V4.nc.tif",
        "OMNO2d_HRM/OMI_trno2_0.10x0.10_200901_Col3_V4.nc.tif",
        "detections-plane/ny/2020_01_09.geojson",
        "detections-plane/ny/2020_01_21.geojson",
        "detections-plane/ny/2020_02_02.geoson",
        "detections-ship/ny/2020_01_09.geojson",
        "detections-ship/ny/2020_01_21.geojson",
        "detections-ship/ny/2020_02_02.geoson",
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
        datetime(2019, 1, 1), "%Y-%m-%dT%H:%M:%SZ"
    )
    assert dataset_info["domain"][1] == datetime.strftime(
        datetime(2019, 6, 1), "%Y-%m-%dT%H:%M:%SZ"
    )


@mock_s3
def test_euports_dataset(app):

    _setup_s3()

    response = app.get("/v1/datasets/du")
    assert response.status_code == 200

    content = json.loads(response.content)
    assert "datasets" in content

    dataset_info = [d for d in content["datasets"] if d["id"] == "nightlights-hd"][0]
    assert dataset_info["domain"][0] == datetime.strftime(
        datetime(2020, 5, 1), "%Y-%m-%dT%H:%M:%SZ"
    )
    assert dataset_info["domain"][1] == datetime.strftime(
        datetime(2020, 7, 1), "%Y-%m-%dT%H:%M:%SZ"
    )

    assert "_du_" in dataset_info["source"]["tiles"][0]

    # Dunkirk has two different datasets under two different spotlight names:
    # "du" and "EUports" - both need to be tested individually

    dataset_info = [d for d in content["datasets"] if d["id"] == "nightlights-viirs"][0]
    assert "_EUPorts_" in dataset_info["source"]["tiles"][0]


@mock_s3
def test_detections_datasets(app):
    """test /datasets endpoint"""

    # aws mocked resources
    _setup_s3()

    response = app.get("v1/datasets/ny")
    assert response.status_code == 200

    content = json.loads(response.content)
    assert "datasets" in content

    dataset_info = [d for d in content["datasets"] if d["id"] == "detections-plane"][0]
    assert len(dataset_info["domain"]) > 2


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
    assert len(dataset_info["domain"]) > 2
    assert dataset_info["domain"][0] == datetime.strftime(
        datetime(2020, 1, 29), "%Y-%m-%dT%H:%M:%SZ"
    )
    assert dataset_info["domain"][-1] == datetime.strftime(
        datetime(2020, 3, 2), "%Y-%m-%dT%H:%M:%SZ"
    )

    assert "&rescale=-100%2C100" not in dataset_info["source"]["tiles"][0]


@mock_s3
def test_global_datasets(app):
    """test /datasets endpoint"""

    # aws mocked resources
    _setup_s3()

    response = app.get("/v1/datasets/global")
    assert response.status_code == 200

    content = json.loads(response.content)
    assert "datasets" in content

    dataset_info = [d for d in content["datasets"] if d["id"] == "no2"][0]
    assert len(dataset_info["domain"]) == 2


@mock_s3
def test_incorrect_dataset_id(app):
    _setup_s3(empty=True)
    response = app.get("/v1/datasets/NOT_A_VALID_DATASET")
    assert response.status_code == 404


def test_full_(app):
    response = app.get("v1/datasets/be")
    print(response)
    assert False
    exit()
