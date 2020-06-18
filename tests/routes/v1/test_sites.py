"""Test /v1/sites endpoints"""

import boto3
from moto import mock_s3
from covid_api.core.config import INDICATOR_BUCKET


@mock_s3
def test_sites(app):
    """test /sites endpoint"""

    # aws mocked resources
    s3 = boto3.client("s3")
    s3.create_bucket(Bucket=INDICATOR_BUCKET)
    s3.put_object(
        Bucket=INDICATOR_BUCKET, Key="indicators/test/super.csv", Body=b"test"
    )

    response = app.get("/v1/sites")
    assert response.status_code == 200


@mock_s3
def test_site_id(app):
    """test /sites/{id} endpoint"""

    # aws mocked resources
    s3 = boto3.client("s3")
    s3.create_bucket(Bucket=INDICATOR_BUCKET)
    s3.put_object(
        Bucket=INDICATOR_BUCKET, Key="indicators/test/super.csv", Body=b"test"
    )

    response = app.get("/v1/sites/be")
    assert response.status_code == 200
