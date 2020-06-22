"""Db tools."""

import boto3
import csv
import json
from datetime import datetime
from typing import Dict, List

from covid_api.core.config import INDICATOR_BUCKET, DT_FORMAT
from covid_api.models.static import IndicatorObservation

s3 = boto3.client("s3")


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
    return [obj["Prefix"].split("/")[1] for obj in response["CommonPrefixes"]]


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
                indicator["notes"] = site_metadata.get("notes", None)
                indicator["highlight_bands"] = site_metadata.get(
                    "highlight_bands", None
                )
            except Exception as e:
                print(e)
                pass

            indicators.append(indicator)

    return indicators
