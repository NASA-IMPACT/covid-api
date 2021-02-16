"""``pytest`` configuration."""

import os

import pytest
import rasterio
from rasterio.io import DatasetReader

from starlette.testclient import TestClient


@pytest.fixture(autouse=True)
def aws_credentials(monkeypatch):
    monkeypatch.setenv("DISABLE_CACHE", "YESPLEASE")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "jqt")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "rde")


@pytest.fixture
def app() -> TestClient:
    """Make sure we use monkeypatch env."""

    from covid_api.main import app

    return TestClient(app)


def mock_rio(src_path: str) -> DatasetReader:
    """Mock rasterio.open."""
    prefix = os.path.join(os.path.dirname(__file__), "fixtures")
    assert src_path.startswith("https://myurl.com/")
    return rasterio.open(os.path.join(prefix, "cog.tif"))


@pytest.fixture
def dataset_manager(monkeypatch):

    from covid_api.db.static.datasets import DatasetManager

    return DatasetManager
