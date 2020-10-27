"""Dataset endpoints."""
from covid_api.api import utils
from covid_api.core import config
from covid_api.db.memcache import CacheLayer
from covid_api.db.static.datasets import datasets
from covid_api.db.static.errors import InvalidIdentifier
from covid_api.models.static import Datasets

from fastapi import APIRouter, Depends, HTTPException, Response

from starlette.requests import Request

router = APIRouter()


@router.get(
    "/datasets",
    responses={200: dict(description="return a list of all available datasets")},
    response_model=Datasets,
)
def get_datasets(
    request: Request,
    response: Response,
    cache_client: CacheLayer = Depends(utils.get_cache),
):
    """Return a list of datasets."""
    dataset_hash = utils.get_hash(spotlight_id="all")
    content = None

    if cache_client:
        content = cache_client.get_dataset_from_cache(dataset_hash)
        if content:
            content = Datasets.parse_raw(content)
            response.headers["X-Cache"] = "HIT"
    if not content:
        scheme = request.url.scheme
        host = request.headers["host"]
        if config.API_VERSION_STR:
            host += config.API_VERSION_STR

        content = datasets.get_all(api_url=f"{scheme}://{host}")

        if cache_client and content:
            cache_client.set_dataset_cache(dataset_hash, content)

    return content


@router.get(
    "/datasets/{spotlight_id}",
    responses={
        200: dict(description="return datasets available for a given spotlight")
    },
    response_model=Datasets,
)
def get_dataset(
    request: Request,
    spotlight_id: str,
    response: Response,
    cache_client: CacheLayer = Depends(utils.get_cache),
):
    """Return dataset info for all datasets available for a given spotlight"""
    try:
        dataset_hash = utils.get_hash(spotlight_id=spotlight_id)
        content = None

        if cache_client:
            content = cache_client.get_dataset_from_cache(dataset_hash)
            if content:
                content = Datasets.parse_raw(content)
                response.headers["X-Cache"] = "HIT"
        if not content:
            scheme = request.url.scheme
            host = request.headers["host"]
            if config.API_VERSION_STR:
                host += config.API_VERSION_STR

            content = datasets.get(spotlight_id, api_url=f"{scheme}://{host}")

            if cache_client and content:
                cache_client.set_dataset_cache(dataset_hash, content)

        return content
    except InvalidIdentifier:
        raise HTTPException(
            status_code=404, detail=f"Invalid spotlight identifier: {spotlight_id}"
        )
