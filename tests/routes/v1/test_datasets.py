"""Test /v1/datasets endpoints"""

import boto3
from datetime import datetime
from moto import mock_s3
from covid_api.core.config import INDICATOR_BUCKET, MT_FORMAT


@mock_s3
def test_sites(app):
    """test /datasets endpoint"""

    # aws mocked resources
    s3 = boto3.client("s3")
    s3.create_bucket(Bucket=INDICATOR_BUCKET)
    s3.put_object(
        Bucket=INDICATOR_BUCKET,
        Key="xco2/GOSAT_XCO2_201901_be_BG_circle_cog.tif",
        Body=b"test",
    )
    s3.put_object(
        Bucket=INDICATOR_BUCKET,
        Key="xco2/GOSAT_XCO2_201904_be_BG_circle_cog.tif",
        Body=b"test",
    )
    s3.put_object(
        Bucket=INDICATOR_BUCKET,
        Key="xco2/GOSAT_XCO2_201906_be_BG_circle_cog.tif",
        Body=b"test",
    )

    response = app.get("/v1/datasets/be")
    assert response.status_code == 200

    dataset_info = [d for d in response.content["datasets"] if d["id"] == "be"][0]
    assert dataset_info["domain"][0] == datetime.strftime(
        datetime.strptime("201901", MT_FORMAT), "%Y-%m-%dT%H%M%S"
    )
    assert dataset_info["domain"][1] == datetime.strftime(
        datetime.strptime("201906", MT_FORMAT), "%Y-%m-%dT%H%M%S"
    )
