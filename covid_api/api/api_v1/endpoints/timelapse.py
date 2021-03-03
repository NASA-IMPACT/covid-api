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
    if query.type == "modis-vi":
        url = f"s3://modis-vi-nasa/MOD13A1.006/2018.01.01.tif"
    else:
        url = f"s3://covid-eo-data/xco2-mean/xco2_16day_mean.{query.month}.tif"
    mean, median = get_zonal_stat(query.geojson, url)
    return dict(mean=mean, median=median)
