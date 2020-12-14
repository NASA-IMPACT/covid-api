"""Test class for metadata generator lambda"""
from datetime import datetime


def test_datasets(gather_datasets_metadata, datasets, sites, bucket):
    """Tests for basic (/) query"""

    content = gather_datasets_metadata(datasets, sites)

    assert content is not None

    assert "global" in content.keys()
    assert "tk" in content.keys()


def test_global_datasets(gather_datasets_metadata, datasets, sites, bucket):
    """Test for correct extraction of global datasets"""
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


def test_periodic_daily_global_datasets(
    gather_datasets_metadata, datasets, sites, bucket
):
    """Test domain of periodic (domain only contains start and stop
    date) global datasets"""
    content = gather_datasets_metadata(datasets, sites)

    assert content is not None

    dataset_info = content["global"]["co2"]

    assert dataset_info["domain"][0] == datetime.strftime(
        datetime(2019, 1, 1), "%Y-%m-%dT%H:%M:%SZ"
    )
    assert dataset_info["domain"][1] == datetime.strftime(
        datetime(2019, 6, 1), "%Y-%m-%dT%H:%M:%SZ"
    )


def test_non_periodic_daily_spotlight_dataset(
    gather_datasets_metadata, datasets, sites, bucket
):
    """Test non periodic (domain has all available dates) spotlight
    sepecific datasets
    """
    content = gather_datasets_metadata(datasets, sites)

    assert content is not None
    assert "ny" in content

    dataset_info = content["ny"]["detections-plane"]

    assert len(dataset_info["domain"]) > 2


def test_euports_datasets(gather_datasets_metadata, datasets, sites, bucket):
    """Test that an EUPorts datasets (du) searchs both for it's own spotlight id
    AND EUPorts"""

    content = gather_datasets_metadata(datasets, sites)

    assert "du" in content
    assert set(content["du"].keys()) == {
        "nightlights-hd",
        "nightlights-viirs",
    }
