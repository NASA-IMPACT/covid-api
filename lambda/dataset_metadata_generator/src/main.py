import json
import os
import re
from datetime import datetime
from typing import List, Optional, Set, Union

import boto3
from exceptions import NoDatesFound

BASE_PATH = os.path.abspath(__file__)
BUCKET_NAME = "covid-eo-data"
s3 = boto3.resource("s3")
bucket = s3.Bucket(BUCKET_NAME)

DT_FORMAT = "%Y-%m-%d"
MT_FORMAT = "%Y%m"
DATASET_METADATA_FILENAME = os.environ.get(
    "DATASET_METADATA_FILENAME", "dev-dataset-metadata.json"
)


def handler(event, context):
    # TODO: defined TypedDicts for these!
    datasets = _gather_json_data("datasets")
    sites = _gather_json_data("sites")

    metadata = {}

    for dataset in datasets:
        if not dataset.get("s3_location"):
            continue

        domain_args = {
            "dataset_folder": dataset["s3_location"],
            "is_periodic": dataset["is_periodic"],
        }
        if _is_global_dataset(dataset):
            metadata.setdefault("global", {}).update(
                {dataset["id"]: {"domain": _get_dataset_domain(**domain_args)}}
            )

        for site in sites:
            domain_args["spotlight_id"] = site["id"]

            if site["id"] in ["du", "gh"]:
                domain_args["spotligt_id"] = ["du", "gh", "EUPorts"]
            try:
                metadata.setdefault(site["id"], {}).update(
                    {dataset["id"]: {"domain": _get_dataset_domain(**domain_args)}}
                )
            # skip adding dataset to metadata object if no dates were found for the given
            # spotlight (indicates dataset is not valid for that spotlight)
            except NoDatesFound:
                pass

    bucket.put_object(
        Body=json.dumps(metadata),
        Key=DATASET_METADATA_FILENAME,
        ContentType="application/json",
    )


def _gather_json_data(dirname):

    results = []
    for filename in os.listdir(os.path.join(BASE_PATH, dirname)):
        if not filename.endswith(".json"):
            continue
        with open(os.path.join(BASE_PATH, dirname, filename)) as f:
            results.append(json.load(f))
    return results


def _is_global_dataset(dataset):
    return any(
        [
            i in dataset["source"]["tiles"][0]
            for i in ["{spotlightId}", "greatlakes", "togo"]
        ]
    )


def _gather_s3_keys(
    spotlight_id: Optional[Union[str, List]] = None, prefix: str = "",
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


# def _get_dataset_folders_by_spotlight(spotlight_id: str) -> Set[str]:
#     """
#     Returns the S3 prefix of datasets containing files for the given spotlight

#     Params:
#     ------
#     spotlight_id (str): id of spotlight to search for

#     Returns:
#     --------
#     set(str)
#     """
#     keys = _gather_s3_keys(spotlight_id=spotlight_id)
#     return {k.split("/")[0] for k in keys}


def _get_dataset_domain(
    dataset_folder: str, is_periodic: bool, spotlight_id: str = None,
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
        result = re.search(
            # matches either dates like: YYYYMM or YYYY_MM_DD
            r"""[^a-zA-Z0-9]((?P<MT_DATE>(\d{6}))|"""
            r"""((?P<YEAR>\d{4})_(?P<MONTH>\d{2})_(?P<DAY>\d{2})))[^a-zA-Z0-9]""",
            key,
            re.IGNORECASE,
        )
        if not result:
            continue

        date = None
        try:
            if result.group("MT_DATE"):
                date = datetime.strptime(result.group("MT_DATE"), MT_FORMAT)
            else:
                datestring = (
                    f"""{result.group("YEAR")}-{result.group("MONTH")}"""
                    f"""-{result.group("DAY")}"""
                )
                date = datetime.strptime(datestring, DT_FORMAT)
        except ValueError:
            # Invalid date value matched - skip date
            continue

        dates.append(date.strftime("%Y-%m-%dT%H:%M:%SZ"))

    if not len(dates) == 0:
        raise NoDatesFound

    if is_periodic:
        return [min(dates), max(dates)]

    return sorted(set(dates))
