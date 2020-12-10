""" Dataset metadata generator lambda. """
import datetime
import json
import os
import re
from typing import List, Optional, Union

import boto3

BASE_PATH = os.path.dirname(os.path.abspath(__file__))
BUCKET_NAME = "covid-eo-data"
s3 = boto3.resource("s3")
bucket = s3.Bucket(BUCKET_NAME)

DT_FORMAT = "%Y-%m-%d"
MT_FORMAT = "%Y%m"
DATASET_METADATA_FILENAME = os.environ.get(
    "DATASET_METADATA_FILENAME", "dev-dataset-metadata.json"
)


def handler(event, context):
    """Reads through the s3 bucket to generate a file that contains
    the datasets for each given spotlight option (_all, global, tk, ny, sf,
    la, be, du, gh) and their respective domain for each spotlight
    Params are standard lambda handler invocation params but not used in
    the context of this lambda's code
    """

    # TODO: defined TypedDicts for these!
    datasets = _gather_json_data("datasets")
    sites = _gather_json_data("sites")

    metadata = {}

    for dataset in datasets:
        if not dataset.get("s3_location"):
            continue

        domain_args = {
            "dataset_folder": dataset["s3_location"],
            "is_periodic": dataset.get("is_periodic"),
            "time_unit": dataset.get("time_unit"),
        }

        domain = _get_dataset_domain(**domain_args)

        metadata.setdefault("_all", {}).update({dataset["id"]: {"domain": domain}})

        if _is_global_dataset(dataset):

            metadata.setdefault("global", {}).update(
                {dataset["id"]: {"domain": domain}}
            )
            continue

        for site in sites:
            domain_args["spotlight_id"] = site["id"]

            if site["id"] in ["du", "gh"]:
                domain_args["spotlight_id"] = ["du", "gh", "EUPorts"]

            # skip adding dataset to metadata object if no dates were found for the given
            # spotlight (indicates dataset is not valid for that spotlight)
            if domain := _get_dataset_domain(**domain_args):
                metadata.setdefault(site["id"], {}).update(
                    {dataset["id"]: {"domain": domain}}
                )

    bucket.put_object(
        Body=json.dumps(metadata),
        Key=DATASET_METADATA_FILENAME,
        ContentType="application/json",
    )
    return json.dumps(metadata)


def _gather_json_data(dirname: str) -> List[dict]:
    """Gathers all JSON files from within a diven directory"""

    results = []

    for filename in os.listdir(os.path.join(BASE_PATH, dirname)):
        if not filename.endswith(".json"):
            continue
        with open(os.path.join(BASE_PATH, dirname, filename)) as f:
            results.append(json.load(f))
    return results


def _is_global_dataset(dataset: dict) -> bool:
    """Returns wether the given dataset is spotlight specific (FALSE)
    or non-spotlight specific (TRUE)"""
    return not any(
        [
            i in dataset["source"]["tiles"][0]
            for i in ["{spotlightId}", "greatlakes", "togo"]
        ]
    )


def _gather_s3_keys(
    spotlight_id: Optional[Union[str, List]] = None, prefix: Optional[str] = "",
) -> List[str]:
    """
    Returns a set of S3 keys. If no args are provided, the keys will represent
    the entire S3 bucket.
    Params:
    -------
    spotlight_id (Optional[str]):
        Id of a spotlight to filter keys by
    prefix (Optional[str]):
        S3 Prefix under which to gather keys, used to specifcy a specific
        dataset folder to search within.

    Returns:
    -------
    set(str)

    """

    keys = [x.key for x in bucket.objects.filter(Prefix=prefix)]

    if not spotlight_id:
        return keys

    if isinstance(spotlight_id, list):
        spotlight_id = "|".join([s for s in spotlight_id])

    pattern = re.compile(rf"""[^a-zA-Z0-9]({spotlight_id})[^a-zA-Z0-9]""")
    return list({key for key in keys if pattern.search(key, re.IGNORECASE,)})


def _get_dataset_domain(
    dataset_folder: str,
    is_periodic: bool,
    spotlight_id: Optional[Union[str, List]] = None,
    time_unit: Optional[str] = "day",
):
    """
    Returns a domain for a given dataset as identified by a folder. If a
    time_unit is passed as a function parameter, the function will assume
    that the domain is periodic and with only return the min/max dates,
    otherwise ALL dates available for that dataset/spotlight will be returned.

    Params:
    ------
    dataset_folder (str): dataset folder to search within
    time_unit (Optional[str]): time_unit from the dataset's metadata json file
    spotlight_id (Optional[str]): a dictionary containing the
        `spotlight_id` of a spotlight to restrict the
        domain search to.
    time_unit (Optional[str] - one of ["day", "month"]):
        Wether the {date} object in the S3 filenames should be matched
        to YYYY_MM_DD (day) or YYYYMM (month)

    Return:
    ------
    List[datetime]
    """
    s3_keys_args = {"prefix": dataset_folder}
    if spotlight_id:
        s3_keys_args["spotlight_id"] = spotlight_id

    keys = _gather_s3_keys(**s3_keys_args)
    dates = []

    for key in keys:

        # matches either dates like: YYYYMM or YYYY_MM_DD
        pattern = re.compile(
            r"[^a-zA-Z0-9]((?P<YEAR>\d{4})_(?P<MONTH>\d{2})_(?P<DAY>\d{2}))[^a-zA-Z0-9]"
        )
        if time_unit == "month":
            pattern = re.compile(
                r"[^a-zA-Z0-9](?P<YEAR>(\d{4}))(?P<MONTH>(\d{2}))[^a-zA-Z0-9]"
            )

        result = pattern.search(key, re.IGNORECASE,)

        if not result:
            continue

        date = None
        try:
            date = datetime.datetime(
                int(result.group("YEAR")),
                int(result.group("MONTH")),
                int(result.groupdict().get("DAY", 1)),
            )

        except ValueError:
            # Invalid date value matched - skip date
            continue

        # Some files happen to have 6 consecutive digits (likely an ID of sorts)
        # that sometimes gets matched as a date. This further restriction of
        # matched timestamps will reduce the number of "false" positives (although
        # ID's between 201011 and 203011 will slip by)
        if not datetime.datetime(2010, 1, 1) < date < datetime.datetime(2030, 1, 1):
            continue

        dates.append(date.strftime("%Y-%m-%dT%H:%M:%SZ"))

    if is_periodic and len(dates):
        return [min(dates), max(dates)]

    return sorted(set(dates))
