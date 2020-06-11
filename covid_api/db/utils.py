"""Db tools."""

import boto3
import csv
import json
from datetime import datetime
from typing import Union, List

from covid_api.core.config import INDICATOR_BUCKET, DT_FORMAT
from covid_api.models.static import IndicatorObservation

s3 = boto3.client("s3")


def s3_get(bucket: str, key: str):
    """Get AWS S3 Object."""
    response = s3.get_object(Bucket=bucket, Key=key)
    return response["Body"].read()


def get_indicator_notes(identifier: str, folder: str) -> Union[str, None]:
    """Get Indicator notes."""
    try:
        key = f"indicators/{folder}/{identifier}.txt"
        return s3_get(INDICATOR_BUCKET, key).strip()
    except Exception:
        return None


def indicator_folders() -> List:
    """Get Indicator folders."""
    response = s3.list_objects_v2(
        Bucket=INDICATOR_BUCKET, Prefix="indicators/", Delimiter="/",
    )
    return [obj["Prefix"].split("/")[1] for obj in response["CommonPrefixes"]]


def get_indicators(identifier) -> List:
    """Return indicators info."""
    indicators = []
    for folder in indicator_folders():
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
            indicator_lines = indicator_csv.decode("utf-8").split()
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

            notes = get_indicator_notes(identifier, folder)

            # construct the final indicator object
            indicators.append(
                dict(
                    id=folder,
                    domain=dict(
                        date=[
                            min(
                                data,
                                key=lambda x: datetime.strptime(x["date"], DT_FORMAT),
                            )["date"],
                            max(
                                data,
                                key=lambda x: datetime.strptime(x["date"], DT_FORMAT),
                            )["date"],
                        ],
                        indicator=[
                            min(data, key=lambda x: x["indicator"])["indicator"],
                            max(data, key=lambda x: x["indicator"])["indicator"],
                        ],
                    ),
                    data=data,
                    notes=notes,
                    **top_level_fields,
                )
            )
        except Exception as e:
            print(e)
            pass

    return indicators
