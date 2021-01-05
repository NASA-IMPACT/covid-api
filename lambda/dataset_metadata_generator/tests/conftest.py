"""
Test configuration class for the dataset metadata generator lambda's unit tests
"""

import pytest

from . import DATASETS, SITES


@pytest.fixture(autouse=True)
def aws_credentials(monkeypatch):
    """Make sure we use monkeypatch env."""
    monkeypatch.setenv("DISABLE_CACHE", "YESPLEASE")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "jqt")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "rde")
    monkeypatch.setenv("DATA_BUCKET_NAME", "covid-eo-data")
    monkeypatch.setenv("DATASET_METADATA_FILENAME", "dev-dataset-metadata.json")


@pytest.fixture
def gather_datasets_metadata():
    """Yield the main function to unit test"""
    # Why is this imported here?
    # See: https://github.com/spulec/moto#what-about-those-pesky-imports

    from ..src.main import _gather_datasets_metadata

    return _gather_datasets_metadata


@pytest.fixture
def datasets():
    """Dataset metadata items"""
    return DATASETS


@pytest.fixture
def sites():
    """Site metadata items"""
    return SITES
