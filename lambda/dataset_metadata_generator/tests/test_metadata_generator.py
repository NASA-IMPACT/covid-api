"""Test class for metadata generator lambda"""
import json
from datetime import datetime


def test_databases(bucket, handler):
    """Tests for basic (/) query"""

    result = handler({}, {})

    assert result is not None

    content = json.loads(result)
    assert "global" in content.keys()
    assert "tk" in content.keys()


def test_datasets_monthly(bucket, handler):
    """Tests wether "monthly" dataset domain is correctly extracted"""
    result = handler({}, {})

    assert result is not None

    content = json.loads(result)
    dataset_info = content["global"]["co2"]

    assert dataset_info["domain"][0] == datetime.strftime(
        datetime(2019, 1, 1), "%Y-%m-%dT%H:%M:%SZ"
    )
    assert dataset_info["domain"][1] == datetime.strftime(
        datetime(2019, 6, 1), "%Y-%m-%dT%H:%M:%SZ"
    )


def test_detections_datasets(bucket, handler):
    """" Tests wether non-periodic dataset domain is correctly extracted"""
    result = handler({}, {})

    assert result is not None

    content = json.loads(result)
    dataset_info = content["ny"]["detections-plane"]

    assert len(dataset_info["domain"]) > 2


def test_datasets_daily(bucket, handler):
    """test /datasets endpoint"""

    # aws mocked resources
    result = handler({}, {})

    assert result is not None

    content = json.loads(result)
    dataset_info = content["tk"]["water-chlorophyll"]

    assert len(dataset_info["domain"]) > 2
    assert dataset_info["domain"][0] == datetime.strftime(
        datetime(2020, 1, 29), "%Y-%m-%dT%H:%M:%SZ"
    )
    assert dataset_info["domain"][-1] == datetime.strftime(
        datetime(2020, 3, 2), "%Y-%m-%dT%H:%M:%SZ"
    )
