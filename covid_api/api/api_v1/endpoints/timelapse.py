"""API metadata."""

from fastapi import APIRouter

from covid_api.models.timelapse import TimelapseValue, TimelapseRequest
from covid_api.api.utils import get_zonal_stat
from covid_api.core import config
from covid_api.db.static.datasets import datasets

router = APIRouter()

@router.post(
    "/timelapse",
    responses={200: {"description": "Return timelapse values for a given geometry"}},
    response_model=TimelapseValue,
)
def timelapse(query: TimelapseRequest):
    """Handle /timelapse requests."""
    dataset = datasets._data[query.type]
    url = f"s3://{config.BUCKET}/{dataset.s3_location}/3B-DAY.MS.MRG.3IMERG.{query.month}-S000000-E235959.V06.tif"
    mean, median = get_zonal_stat(query.geojson, url)
    return dict(mean=mean, median=median)
