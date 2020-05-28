"""Test /v1/sites endpoints"""
import os
import boto3
import pytest
from moto import mock_s3
from covid_api.core.config import INDICATOR_BUCKET

def test_sites(app):
    """test /sites endpoint"""
    response = app.get("/v1/sites")
    assert response.status_code == 200

@pytest.fixture(scope='function')
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'

@pytest.fixture(scope='function')
def s3(aws_credentials):
    with mock_s3():
        yield boto3.client('s3', region_name='us-east-1')

def test_site_id(app, aws_credentials, s3):
    """test /sites/{id} endpoint"""

    # aws mocked resources
    s3.create_bucket(Bucket=INDICATOR_BUCKET)
    s3.put_object(Bucket=INDICATOR_BUCKET, Key='indicators/test/super.csv', Body=b'test')

    response = app.get("/v1/sites/be")
    assert response.status_code == 200
