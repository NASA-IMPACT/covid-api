import os

import boto3
import pytest
from moto import mock_s3

INDICATOR_BUCKET = "covid-eo-data"


@pytest.fixture(autouse=True)
def aws_credentials():
    """Make sure we use monkeypatch env."""
    os.environ["DISABLE_CACHE"] = "YESPLEASE"
    os.environ["AWS_ACCESS_KEY_ID"] = "jqt"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "rde"


@pytest.fixture
def s3(aws_credentials):
    with mock_s3():
        yield boto3.client("s3", region_name="us-east-1")


@pytest.fixture
def handler():
    # Why is this imported here?
    # See: https://github.com/spulec/moto#what-about-those-pesky-imports
    from ..src.main import handler

    yield handler


@pytest.fixture
def empty_bucket(s3):
    bucket = s3.create_bucket(Bucket=INDICATOR_BUCKET)
    yield bucket


@pytest.fixture
def bucket(s3, empty_bucket):

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
    yield empty_bucket
