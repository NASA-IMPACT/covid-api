"""``pytest`` configuration."""

import os
import pytest
import boto3
from moto import mock_s3

from starlette.testclient import TestClient

import rasterio
from rasterio.io import DatasetReader

from covid_api.core.config import INDICATOR_BUCKET

@mock_s3
@pytest.fixture(autouse=True)
def app(monkeypatch) -> TestClient:
    """Make sure we use monkeypatch env."""
    monkeypatch.setenv("DISABLE_CACHE", "YESPLEASE")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "jqt")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "rde")

    s3 = boto3.client("s3")
    s3.create_bucket(Bucket=INDICATOR_BUCKET)
    s3.put_object(
        Bucket=INDICATOR_BUCKET, Key="detections/plane/detection_scenes.csv", Body=b"test"
    )

    from covid_api.main import app

    return TestClient(app)


def mock_rio(src_path: str) -> DatasetReader:
    """Mock rasterio.open."""
    prefix = os.path.join(os.path.dirname(__file__), "fixtures")
    assert src_path.startswith("https://myurl.com/")
    return rasterio.open(os.path.join(prefix, "cog.tif"))
