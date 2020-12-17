"""
Test configuration class for the dataset metadata generator lambda's unit tests
"""

import os

import boto3
import pytest
from moto import mock_s3

from . import DATASETS, SITES

INDICATOR_BUCKET = "covid-eo-data"


@pytest.fixture(autouse=True)
def aws_credentials():
    """Make sure we use monkeypatch env."""
    os.environ["DISABLE_CACHE"] = "YESPLEASE"
    os.environ["AWS_ACCESS_KEY_ID"] = "jqt"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "rde"


@pytest.fixture
def s3(aws_credentials):
    """Yields a mocked boto3 s3 client"""
    with mock_s3():
        yield boto3.client("s3", region_name="us-east-1")


@pytest.fixture
def gather_datasets_metadata():
    """Yield the main function to unit test"""
    # Why is this imported here?
    # See: https://github.com/spulec/moto#what-about-those-pesky-imports
    from ..src.main import _gather_datasets_metadata

    yield _gather_datasets_metadata


@pytest.fixture
def datasets():
    """Dataset metadata items"""
    yield DATASETS


@pytest.fixture
def sites():
    """Site metadata items"""
    yield SITES


@pytest.fixture
def empty_bucket(s3):
    """Yields an empty mocked s3 bucket"""
    bucket = s3.create_bucket(Bucket=INDICATOR_BUCKET)
    yield bucket


@pytest.fixture
def bucket(s3, empty_bucket):
    """Yields a bucket pre-populated with empty files to parse for date
    domain extraction"""
    s3_keys = [
        "xco2-mean/GOSAT_XCO2_2019_01_01_be_BG_circle_cog.tif",
        "xco2-mean/GOSAT_XCO2_2019_04_01_be_BG_circle_cog.tif",
        "xco2-mean/GOSAT_XCO2_2019_06_01_be_BG_circle_cog.tif",
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
    # empty_bucket is now full. I wish there was a better way to do this...
    yield empty_bucket
