import os
import json

BASE_PATH = os.path.abspath(__file__)


def handler(event, context):
    # TODO: defined TypedDicts for these!
    datasets = _gather_json_data("datasets")
    sites = _gather_json_data("sites")

    for dataset in datasets:
        if not dataset["s3_location"]:
            continue

        domain_args = {
            "dataset_folder": dataset["s3_location"],
            "is_periodic": dataset["is_periodic"],
        }
        if not _is_global_dataset(dataset):
            dataset["domain"] = get_dataset_domain(**domain_args)

    global_datasets = _get_global_datasets(datasets)
    for dataset in global_datasets:
        if not dataset["s3_location"]:
            continue
        #  domain_args: Dict[str, Any] = {
        #     "dataset_folder": dataset.s3_location,
        #     "is_periodic": dataset.is_periodic,
        # }
        # if spotlight_id:
        #     domain_args["spotlight_id"] = spotlight_id

        dataset["domain"] = get_dataset_domain(
            dataset_folder=dataset["s3_location"], is_periodic=dataset["is_periodic"]
        )

    raise NotImplementedError


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


def _get_global_datasets(datasets):
    """
        Returns all datasets which do not reference a specific spotlight, by
        filtering out datasets where the "source.tiles" value contains either
        `spotlightId`.
        """

    return {
        k: v
        for k, v in datasets.items()
        if not any(
            i in v.source.tiles[0] for i in ["{spotlightId}", "greatlakes", "togo"]
        )
    }


def gather_s3_keys(
    spotlight_id: Optional[str] = None, prefix: Optional[str] = None,
) -> Set[str]:
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
    keys: set = set()

    list_objects_args = {"Bucket": INDICATOR_BUCKET}

    if prefix:
        list_objects_args["Prefix"] = prefix

    response = s3.list_objects_v2(**list_objects_args)
    keys.update({x["Key"] for x in response.get("Contents", [])})

    while response["IsTruncated"]:

        list_objects_args["ContinuationToken"] = response["NextContinuationToken"]
        response = s3.list_objects_v2(**list_objects_args)

        keys.update({x["Key"] for x in response.get("Contents", [])})

    if not spotlight_id:
        return keys

    return {
        key
        for key in keys
        if re.search(
            rf"""[^a-zA-Z0-9]({spotlight_id})[^a-zA-Z0-9]""", key, re.IGNORECASE,
        )
    }


def get_dataset_folders_by_spotlight(spotlight_id: str) -> Set[str]:
    """
    Returns the S3 prefix of datasets containing files for the given spotlight

    Params:
    ------
    spotlight_id (str): id of spotlight to search for

    Returns:
    --------
    set(str)
    """
    keys = gather_s3_keys(spotlight_id=spotlight_id)
    return {k.split("/")[0] for k in keys}


def get_dataset_domain(
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

    keys = gather_s3_keys(**s3_keys_args)
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
            # Invalid date value matched
            continue

        dates.append(date.strftime("%Y-%m-%dT%H:%M:%SZ"))

    if is_periodic and len(dates):
        return [min(dates), max(dates)]

    return sorted(set(dates))


def s3_get(bucket: str, key: str):
    """Get AWS S3 Object."""
    response = s3.get_object(Bucket=bucket, Key=key)
    return response["Body"].read()
