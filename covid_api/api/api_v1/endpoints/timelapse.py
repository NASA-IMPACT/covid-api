"""API metadata."""

from covid_api.api.utils import get_zonal_stat
from covid_api.models.timelapse import TimelapseRequest, TimelapseValue

from fastapi import APIRouter

router = APIRouter()


@router.post(
    "/timelapse",
    responses={200: {"description": "Return timelapse values for a given geometry"}},
    response_model=TimelapseValue,
)
def timelapse(query: TimelapseRequest):
    """Handle /timelapse requests."""
    url = f"https://modis-vi-nasa.s3.amazonaws.com/MOD13A1.006/{query.month}.tif"
    mean, median = get_zonal_stat(query.geojson, url)
    return dict(mean=mean, median=median)
