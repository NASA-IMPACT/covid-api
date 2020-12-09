import json
from datetime import datetime


def test_databases(bucket, handler):

    result = handler({}, {})

    assert result is not None

    content = json.loads(result)
    assert "global" in content.keys()
    assert "tk" in content.keys()


def test_datasets_monthly(bucket, handler):
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


# def test_euports_dataset(app):

#     _setup_s3()

#     response = app.get("/v1/datasets/du")
#     assert response.status_code == 200

#     content = json.loads(response.content)
#     assert "datasets" in content

#     dataset_info = [d for d in content["datasets"] if d["id"] == "nightlights-hd"][0]
#     assert dataset_info["domain"][0] == datetime.strftime(
#         datetime(2020, 5, 1), "%Y-%m-%dT%H:%M:%SZ"
#     )
#     assert dataset_info["domain"][1] == datetime.strftime(
#         datetime(2020, 7, 1), "%Y-%m-%dT%H:%M:%SZ"
#     )

#     assert "_du_" in dataset_info["source"]["tiles"][0]

#     # Dunkirk has two different datasets under two different spotlight names:
#     # "du" and "EUports" - both need to be tested individually

#     dataset_info = [d for d in content["datasets"] if d["id"] == "nightlights-viirs"][0]
#     assert "_EUPorts_" in dataset_info["source"]["tiles"][0]


# @mock_s3
# def test_detections_datasets(app):
#     """test /datasets endpoint"""

#     # aws mocked resources
#     _setup_s3()

#     response = app.get("v1/datasets/ny")
#     assert response.status_code == 200

#     content = json.loads(response.content)
#     assert "datasets" in content

#     dataset_info = [d for d in content["datasets"] if d["id"] == "detections-plane"][0]
#     assert len(dataset_info["domain"]) > 2


# @mock_s3
# def test_datasets_daily(app):
#     """test /datasets endpoint"""

#     # aws mocked resources
#     _setup_s3()

#     response = app.get("/v1/datasets/tk")
#     assert response.status_code == 200

#     content = json.loads(response.content)
#     assert "datasets" in content

#     dataset_info = [d for d in content["datasets"] if d["id"] == "water-chlorophyll"][0]
#     assert len(dataset_info["domain"]) > 2
#     assert dataset_info["domain"][0] == datetime.strftime(
#         datetime(2020, 1, 29), "%Y-%m-%dT%H:%M:%SZ"
#     )
#     assert dataset_info["domain"][-1] == datetime.strftime(
#         datetime(2020, 3, 2), "%Y-%m-%dT%H:%M:%SZ"
#     )

#     assert "&rescale=-100%2C100" not in dataset_info["source"]["tiles"][0]


# @mock_s3
# def test_global_datasets(app):
#     """test /datasets endpoint"""

#     # aws mocked resources
#     _setup_s3()

#     response = app.get("/v1/datasets/global")
#     assert response.status_code == 200

#     content = json.loads(response.content)
#     assert "datasets" in content

#     dataset_info = [d for d in content["datasets"] if d["id"] == "no2"][0]
#     assert len(dataset_info["domain"]) == 2


# @mock_s3
# def test_incorrect_dataset_id(app):
#     _setup_s3(empty=True)
#     response = app.get("/v1/datasets/NOT_A_VALID_DATASET")
#     assert response.status_code == 404
