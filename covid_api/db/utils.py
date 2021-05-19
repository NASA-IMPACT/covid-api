"""Db tools."""

import csv
import json
import os
from datetime import datetime
from typing import Dict, List

import boto3
from botocore import config

from covid_api.core.config import DT_FORMAT, INDICATOR_BUCKET
from covid_api.models.static import IndicatorObservation

s3_params = dict(service_name="s3")
lambda_params = dict(
    service_name="lambda",
    region_name="us-east-1",
    config=config.Config(
        read_timeout=900, connect_timeout=900, retries={"max_attempts": 0}
    ),
)

if os.environ.get("AWS_ENDPOINT_URL"):
    print("Loading from local")
    s3_params["endpoint_url"] = os.environ["AWS_ENDPOINT_URL"]
    lambda_params["endpoint_url"] = os.environ["AWS_ENDPOINT_URL"]

s3 = boto3.client(**s3_params)

_lambda = boto3.client(**lambda_params)


def invoke_lambda(
    lambda_function_name: str, payload: dict = None, invocation_type="RequestResponse"
):
    """Invokes a lambda function using the boto3 lambda client.

    Params:
    -------
    lambda_function_name (str): name of the lambda to invoke
    payload (Optional[dict]): data into invoke the lambda function with (will be accessible
        in the lambda handler function under the `event` param)
    invocation_type (Optional[str] = ["RequestResponse", "Event", "DryRun"]):
        RequestReponse will run the lambda synchronously (holding up the thread
        until the lambda responds
        Event will run asynchronously
        DryRun will only verify that the user/role has the correct permissions to invoke
        the lambda function

    Returns:
    --------
    (dict) Lambda invocation response, see:
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/lambda.html#Lambda.Client.invoke

    - NOTE:
    The current configuration specifies a RequestResponse invocation, which does
    indeed run synchronously, but returns a status succeeded of 202 (Accepted) when
    it should return a 200 status. 202 status is expected from the `Event` invocation
    type (indicated lamdba was initiated but we don't know it's status)

    - NOTE:
    The current configuration should directly return the lambda output under
    response["Payload"]: StreamingBody, however the byte string currently being returned
    contains lambda invocation/runtime details from the logs. (eg:

    ```
    START RequestId: 7c61eb52-735d-1ce4-0df2-a975197924eb Version: 1
    END RequestId: 7c61eb52-735d-1ce4-0df2-a975197924eb
    REPORT RequestId: 7c61eb52-735d-1ce4-0df2-a975197924eb  Init Duration: 232.54 ms        Duration: 3.02 ms       Billed Duration: 100 ms Memory Size: 128 MB    Max Memory Used: 33 MB

    {"result":"success","input":"test"}

    ```
    when we only expect the JSON object: {"result":"success", "input":"test"} to be returned
    )

    To load just the lambda output use:

    ```
    response = r["Payload"].read().decode("utf-8")
    lambda_output = json.loads(
        response[response.index("{") : (response.index("}") + 1)]
    )
    ```
    where r is the output of this function.
    """
    lambda_invoke_params = dict(
        FunctionName=lambda_function_name, InvocationType=invocation_type
    )
    if payload:
        lambda_invoke_params.update(dict(Payload=json.dumps(payload)))
    return _lambda.invoke(**lambda_invoke_params)


def s3_get(bucket: str, key: str):
    """Get AWS S3 Object."""
    response = s3.get_object(Bucket=bucket, Key=key)
    return response["Body"].read()


def get_indicator_site_metadata(identifier: str, folder: str) -> Dict:
    """Get Indicator metadata for a specific site."""
    try:
        key = f"indicators/{folder}/{identifier}.json"
        return json.loads(s3_get(INDICATOR_BUCKET, key))
    except Exception:
        return {}


def indicator_folders() -> List:
    """Get Indicator folders."""
    response = s3.list_objects_v2(
        Bucket=INDICATOR_BUCKET, Prefix="indicators/", Delimiter="/",
    )
    return [obj["Prefix"].split("/")[1] for obj in response.get("CommonPrefixes", [])]


def indicator_exists(identifier: str, indicator: str):
    """Check if an indicator exists for a site"""
    try:
        s3.head_object(
            Bucket=INDICATOR_BUCKET, Key=f"indicators/{indicator}/{identifier}.csv",
        )
        return True
    except Exception:
        try:
            s3.head_object(
                Bucket=INDICATOR_BUCKET,
                Key=f"indicators/{indicator}/{identifier}.json",
            )
            return True
        except Exception:
            return False


def get_indicators(identifier) -> List:
    """Return indicators info."""
    indicators = []
    for folder in indicator_folders():
        if indicator_exists(identifier, folder):
            indicator = dict(id=folder)
            try:
                data = []
                # metadata for reading the data and converting to a consistent format
                metadata_json = s3_get(
                    INDICATOR_BUCKET, f"indicators/{folder}/metadata.json"
                )
                metadata_dict = json.loads(metadata_json.decode("utf-8"))

                # read the actual indicator data
                indicator_csv = s3_get(
                    INDICATOR_BUCKET, f"indicators/{folder}/{identifier}.csv"
                )
                indicator_lines = indicator_csv.decode("utf-8").split("\n")
                reader = csv.DictReader(indicator_lines,)

                # top level metadata is added directly to the response
                top_level_fields = {
                    k: v for k, v in metadata_dict.items() if isinstance(v, str)
                }

                # for each row (observation), format the data correctly
                for row in reader:
                    date = datetime.strptime(
                        row[metadata_dict["date"]["column"]],
                        metadata_dict["date"]["format"],
                    ).strftime(DT_FORMAT)

                    other_fields = {
                        k: row.get(v["column"], None)
                        for k, v in metadata_dict.items()
                        if isinstance(v, dict) and v.get("column") and k != "date"
                    }

                    # validate and parse the row
                    i = IndicatorObservation(**other_fields)

                    data.append(dict(date=date, **i.dict(exclude_none=True)))

                # add to the indicator dictionary
                indicator["domain"] = dict(
                    date=[
                        min(
                            data, key=lambda x: datetime.strptime(x["date"], DT_FORMAT),
                        )["date"],
                        max(
                            data, key=lambda x: datetime.strptime(x["date"], DT_FORMAT),
                        )["date"],
                    ],
                    indicator=[
                        min(data, key=lambda x: x["indicator"])["indicator"],
                        max(data, key=lambda x: x["indicator"])["indicator"],
                    ],
                )
                indicator["data"] = data
                indicator.update(top_level_fields)

            except Exception as e:
                print(e)
                pass

            try:
                site_metadata = get_indicator_site_metadata(identifier, folder)
                # this will, intentionally, overwrite the name from the data if present
                if "name" in site_metadata:
                    indicator["name"] = site_metadata.get("name")
                indicator["notes"] = site_metadata.get("notes", None)
                indicator["highlight_bands"] = site_metadata.get(
                    "highlight_bands", None
                )
            except Exception as e:
                print(e)
                pass

            indicators.append(indicator)

    return indicators
