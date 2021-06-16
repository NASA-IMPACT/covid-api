"""API metadata."""
import re
from concurrent import futures
from datetime import datetime, timedelta
from typing import List, Union

from dateutil.relativedelta import relativedelta

from covid_api.api.utils import get_zonal_stat
from covid_api.core.config import API_VERSION_STR
from covid_api.db.static.datasets import datasets as _datasets
from covid_api.db.static.errors import InvalidIdentifier
from covid_api.db.static.sites import sites
from covid_api.models.static import Dataset
from covid_api.models.timelapse import TimelapseRequest, TimelapseValue

from fastapi import APIRouter, HTTPException

from starlette.requests import Request

router = APIRouter()


# TODO: validate inputs with typing/pydantic models
def _get_mean_median(query, url, dataset):

    # format S3 URL template with spotlightId, if dataset is
    # spotlight specific
    if "{spotlightId}" in url:
        if not query.spotlight_id:
            raise HTTPException(
                status_code=400,
                detail=f"Must provide a `spotlight_id` for dataset: {dataset.id}",
            )
        url = _insert_spotlight_id(url, query.spotlight_id)
    try:
        mean, median = get_zonal_stat(query.geojson, url)
        return dict(mean=mean, median=median)

    except Exception:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unable to calculate mean/median values. This either due to a bounding box "
                "extending beyond the edges of the COG or there are no COGs available for the "
                "requested date range."
            ),
        )


@router.post(
    "/timelapse",
    responses={200: {"description": "Return timelapse values for a given geometry"}},
    response_model=Union[List[TimelapseValue], TimelapseValue],
    response_model_exclude_none=True,
)
def timelapse(request: Request, query: TimelapseRequest):
    """Handle /timelapse requests."""

    # get dataset metadata for the requested dataset
    # will be used to validate other parts of the query
    dataset = _get_dataset_metadata(request, query)

    # extract S3 URL template from dataset metadata info
    url = _extract_s3_url(dataset)

    if query.date:

        # format S3 URL template with date object
        url = _insert_date(url, dataset, query.date)
        return _get_mean_median(query, url, dataset)

    if query.date_range:

        if dataset.time_unit == "day":
            # Get start and end dates
            start = _validate_query_date(dataset, query.date_range[0])
            end = _validate_query_date(dataset, query.date_range[1])

            # Populate all days in between Add 1 to days to ensure it contains the end date as well
            dates = [
                datetime.strftime((start + timedelta(days=x)), "%Y_%m_%d")
                for x in range(0, (end - start).days + 1)
            ]

        if dataset.time_unit == "month":
            start = datetime.strptime(query.date_range[0], "%Y%m")
            end = datetime.strptime(query.date_range[1], "%Y%m")

            num_months = (end.year - start.year) * 12 + (end.month - start.month)

            dates = [
                datetime.strftime((start + relativedelta(months=+x)), "%Y%m")
                for x in range(0, num_months + 1)
            ]

        with futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_stats_queries = {
                executor.submit(
                    _get_mean_median, query, _insert_date(url, dataset, date), dataset
                ): date
                for date in dates
            }

        stats = []

        for future in futures.as_completed(future_stats_queries):
            date = future_stats_queries[future]
            try:
                stats.append({"date": date, **future.result()})
            except HTTPException as e:
                stats.append({"date": date, "error": e.detail})

        return sorted(stats, key=lambda s: s["date"])


def _get_dataset_metadata(request: Request, query: TimelapseRequest):

    scheme = request.url.scheme
    host = request.headers["host"]

    if API_VERSION_STR:
        host += API_VERSION_STR

    dataset = list(
        filter(
            lambda d: d.id == query.dataset_id,
            _datasets.get_all(api_url=f"{scheme}://{host}").datasets,
        )
    )

    if not dataset:
        raise HTTPException(
            status_code=404, detail=f"No dataset found for id: {query.dataset_id}"
        )

    dataset = dataset[0]

    if dataset.source.type != "raster":
        raise HTTPException(
            status_code=400,
            detail=f"Dataset {query.dataset_id} is not a raster-type dataset",
        )

    return dataset


def _extract_s3_url(dataset: Dataset):
    url_search = re.search(r"url=([^&\s]*)", dataset.source.tiles[0])
    if not url_search:
        raise HTTPException(status_code=500)

    return url_search.group(1)


def _insert_date(url: str, dataset: Dataset, date: str):
    _validate_query_date(dataset, date)
    return url.replace("{date}", date)


def _validate_query_date(dataset: Dataset, date: str):
    date_format = "%Y_%m_%d" if dataset.time_unit == "day" else "%Y%m"
    try:
        return datetime.strptime(date, date_format)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid date format. {date} should be like "
                f"{'YYYYMM' if dataset.time_unit == 'month' else 'YYYY_MM_DD'}"
            ),
        )


def _insert_spotlight_id(url: str, spotlight_id: str):
    if not spotlight_id:
        raise HTTPException(status_code=400, detail="Missing spotlightId")
    try:
        sites.get(spotlight_id)
    except InvalidIdentifier:
        raise HTTPException(
            status_code=404, detail=f"No spotlight found for id: {spotlight_id}"
        )

    return url.replace("{spotlightId}", spotlight_id)
