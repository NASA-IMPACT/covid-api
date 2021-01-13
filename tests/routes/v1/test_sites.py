"""Test /v1/sites endpoints"""

import boto3
from moto import mock_s3

from covid_api.core.config import INDICATOR_BUCKET


@mock_s3
def _setup_s3():
    s3 = boto3.resource("s3")
    bucket = s3.Bucket(INDICATOR_BUCKET)
    bucket.create()
    s3_keys = [
        ("indicators/test/super.csv", b"test"),
    ]
    for key, content in s3_keys:
        bucket.put_object(Body=content, Key=key)
    return bucket


@mock_s3
def test_sites(app):
    _setup_s3()
    """test /sites endpoint"""

    response = app.get("/v1/sites")
    assert response.status_code == 200


@mock_s3
def test_site_id(app):
    _setup_s3()
    """test /sites/{id} endpoint"""

    response = app.get("/v1/sites/be")
    assert response.status_code == 200
