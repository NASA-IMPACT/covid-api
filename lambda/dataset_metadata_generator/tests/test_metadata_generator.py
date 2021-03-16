"""Test class for metadata generator lambda"""
from datetime import datetime

import boto3
from moto import mock_s3


@mock_s3
def _setup_s3():

    s3 = boto3.resource("s3")

    bucket = s3.Bucket("covid-eo-data")
    bucket.create()
    s3_keys = [
        ("indicators/test/super.csv", b"test"),
        ("xco2-mean/GOSAT_XCO2_2019_01_01_be_BG_circle_cog.tif", b"test"),
        ("xco2-mean/GOSAT_XCO2_2019_04_01_be_BG_circle_cog.tif", b"test"),
        ("xco2-mean/GOSAT_XCO2_2019_06_01_be_BG_circle_cog.tif", b"test"),
        ("oc3_chla_anomaly/anomaly-chl-tk-2020_01_29.tif", b"test"),
        ("oc3_chla_anomaly/anomaly-chl-tk-2020_02_05.tif", b"test"),
        ("oc3_chla_anomaly/anomaly-chl-tk-2020_03_02.tif", b"test"),
        ("bm_500m_daily/VNP46A2_V011_be_2020_01_01_cog.tif", b"test"),
        ("bm_500m_daily/VNP46A2_V011_be_2020_02_29_cog.tif", b"test"),
        ("bm_500m_daily/VNP46A2_V011_be_2020_03_20_cog.tif", b"test"),
        ("bm_500m_daily/VNP46A2_V011_EUPorts_2020_01_01_cog.tif", b"test"),
        ("bm_500m_daily/VNP46A2_V011_EUPorts_2020_02_29_cog.tif", b"test"),
        ("bm_500m_daily/VNP46A2_V011_EUPorts_2020_03_20_cog.tif", b"test"),
        ("bmhd_30m_monthly/BMHD_VNP46A2_du_202005_cog.tif", b"test"),
        ("bmhd_30m_monthly/BMHD_VNP46A2_du_202006_cog.tif", b"test"),
        ("bmhd_30m_monthly/BMHD_VNP46A2_du_202007_cog.tif", b"test"),
        ("OMNO2d_HRM/OMI_trno2_0.10x0.10_200401_Col3_V4.nc.tif", b"test"),
        ("OMNO2d_HRM/OMI_trno2_0.10x0.10_200708_Col3_V4.nc.tif", b"test"),
        ("OMNO2d_HRM/OMI_trno2_0.10x0.10_200901_Col3_V4.nc.tif", b"test"),
        ("detections-plane/ny/2020_01_09.geojson", b"test"),
        ("detections-plane/ny/2020_01_21.geojson", b"test"),
        ("detections-plane/ny/2020_02_02.geoson", b"test"),
        ("detections-ship/ny/2020_01_09.geojson", b"test"),
        ("detections-ship/ny/2020_01_21.geojson", b"test"),
        ("detections-ship/ny/2020_02_02.geoson", b"test"),
        ("indicators/test/super.csv", b"test"),
    ]
    for key, content in s3_keys:
        bucket.put_object(Body=content, Key=key)
    return bucket


@mock_s3
def test_datasets(gather_datasets_metadata, datasets, sites):
    """Tests for basic (/) query"""

    _setup_s3()

    content = gather_datasets_metadata(datasets, sites)

    assert content is not None

    assert "global" in content.keys()
    assert "tk" in content.keys()


@mock_s3
def test_global_datasets(gather_datasets_metadata, datasets, sites):
    """Test for correct extraction of global datasets"""

    _setup_s3()

    content = gather_datasets_metadata(datasets, sites)

    assert content is not None

    assert "global" in content
    assert set(content["global"].keys()) == {"co2"}

    assert "_all" in content
    assert set(content["_all"].keys()) == {
        "co2",
        "detections-plane",
        "nightlights-hd",
        "nightlights-viirs",
        "water-chlorophyll",
    }


@mock_s3
def test_periodic_daily_global_datasets(gather_datasets_metadata, datasets, sites):
    """Test domain of periodic (domain only contains start and stop
    date) global datasets"""

    _setup_s3()

    content = gather_datasets_metadata(datasets, sites)

    assert content is not None

    dataset_info = content["global"]["co2"]

    assert dataset_info["domain"][0] == datetime.strftime(
        datetime(2019, 1, 1), "%Y-%m-%dT%H:%M:%SZ"
    )
    assert dataset_info["domain"][1] == datetime.strftime(
        datetime(2019, 6, 1), "%Y-%m-%dT%H:%M:%SZ"
    )


@mock_s3
def test_non_periodic_daily_spotlight_dataset(
    gather_datasets_metadata, datasets, sites
):
    """Test non periodic (domain has all available dates) spotlight
    sepecific datasets
    """

    _setup_s3()

    content = gather_datasets_metadata(datasets, sites)

    assert content is not None
    assert "ny" in content

    dataset_info = content["ny"]["detections-plane"]

    assert len(dataset_info["domain"]) > 2


@mock_s3
def test_euports_datasets(gather_datasets_metadata, datasets, sites):
    """Test that an EUPorts datasets (du) searchs both for it's own spotlight id
    AND EUPorts"""

    _setup_s3()

    content = gather_datasets_metadata(datasets, sites)

    assert "du" in content
    assert set(content["du"].keys()) == {
        "nightlights-hd",
        "nightlights-viirs",
        "water-chlorophyll",
        "detections-plane"
    }
