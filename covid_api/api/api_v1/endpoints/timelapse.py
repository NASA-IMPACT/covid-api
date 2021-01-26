"""API metadata."""
import re
from datetime import datetime

from covid_api.api.api_v1.endpoints.exceptions import (
    InvalidDateFormat,
    MissingSpotlightId,
    NonRasterDataset,
    UnableToExtractS3Url,
)
from covid_api.api.utils import get_zonal_stat
from covid_api.core.config import API_VERSION_STR, DT_FORMAT, MT_FORMAT
from covid_api.db.static.datasets import datasets as _datasets
from covid_api.db.static.errors import InvalidIdentifier
from covid_api.db.static.sites import sites
from covid_api.models.static import Dataset
from covid_api.models.timelapse import TimelapseRequest, TimelapseValue

from fastapi import APIRouter

from starlette.requests import Request

router = APIRouter()


@router.post(
    "/timelapse",
    responses={200: {"description": "Return timelapse values for a given geometry"}},
    response_model=TimelapseValue,
)
def timelapse(request: Request, query: TimelapseRequest):
    """Handle /timelapse requests."""

    # get dataset metadata for the requested dataset
    # will be used to validate other parts of the query
    dataset = _get_dataset_metadata(request, query)

    # extract S3 URL template from dataset metadata info
    url = _extract_s3_url(dataset)

    # format S3 URL template with date object
    url = _insert_date(url, dataset, query.date)

    # format S3 URL template with spotlightId, if dataset is
    # spotlight specific
    if "{spotlightId}" in url:
        url = _insert_spotlight_id(url, query.spotlight_id)

    mean, median = get_zonal_stat(query.geojson, url)
    return dict(mean=mean, median=median)


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
        raise InvalidIdentifier

    dataset = dataset[0]

    if dataset.source.type != "raster":
        raise NonRasterDataset

    return dataset


def _extract_s3_url(dataset: Dataset):
    url_search = re.search(r"url=([^&\s]*)", dataset.source.tiles[0])
    if not url_search:
        raise UnableToExtractS3Url

    return url_search.group(1)


def _insert_date(url: str, dataset: Dataset, date: str):
    _validate_query_date(dataset, date)
    return url.replace("{date}", date)


def _validate_query_date(dataset: Dataset, date: str):
    date_format = DT_FORMAT if dataset.time_unit == "day" else MT_FORMAT
    try:
        datetime.strptime(date, date_format)
    except ValueError:
        raise InvalidDateFormat


def _insert_spotlight_id(url: str, spotlight_id: str):
    if not spotlight_id:
        raise MissingSpotlightId
    try:
        sites.get(spotlight_id)
    except InvalidIdentifier:
        raise

    return url.replace("{spotlightId}", spotlight_id)
