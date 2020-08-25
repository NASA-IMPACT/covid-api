"""Dataset endpoints."""
from typing import Dict

from covid_api.db.static.errors import InvalidIdentifier
from fastapi import APIRouter, HTTPException, Depends, Response

from covid_api.models.static import Datasets
from covid_api.db.static.datasets import datasets
from covid_api.db.memcache import CacheLayer
from covid_api.api import utils

router = APIRouter()


@router.get(
    "/datasets",
    responses={200: dict(description="return a list of all available datasets")},
    response_model=Datasets,
)
def get_datasets(
    response: Response,
    cache_client: CacheLayer = Depends(utils.get_cache),
):
    """Return a list of datasets."""
    dataset_hash = utils.get_hash(spotlight_id='all')
    content = None

    if cache_client:
        try:
            content = cache_client.get_image_from_cache(dataset_hash)
            response.headers = headers["X-Cache"] = "HIT"
        except Exception:
            content = None
    if not content:
        content = datasets.get_all()
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
    spotlight_id: str,
    response: Response,
    cache_client: CacheLayer = Depends(utils.get_cache),
):
    """Return dataset info for all datasets available for a given spotlight"""
    try:
        dataset_hash = utils.get_hash(spotlight_id=spotlight_id)
        content = None

        if cache_client:
            try:
                content = cache_client.get_image_from_cache(dataset_hash)
                response.headers["X-Cache"] = "HIT"
            except Exception:
                content = None
        if not content:
            content = datasets.get(spotlight_id)
            if cache_client and content:
                cache_client.set_dataset_cache(dataset_hash, content)

        return content
    except InvalidIdentifier:
        raise HTTPException(
            status_code=404, detail=f"Invalid spotlight identifier: {spotlight_id}"
        )
