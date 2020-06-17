"""API metadata."""

from fastapi import APIRouter

from covid_api.models.timelapse import TimelapseValue, TimelapseRequest
from covid_api.api.utils import get_zonal_stat

router = APIRouter()


@router.post(
    "/timelapse",
    responses={200: {"description": "Return timelapse values for a given geometry"}},
    response_model=TimelapseValue,
)
def timelapse(query: TimelapseRequest):
    """Handle /timelapse requests."""
    if query.type == "no2":
        url = f"s3://covid-eo-data/OMNO2d_HRM/OMI_trno2_0.10x0.10_{query.month}_Col3_V4.nc.tif"
    else:
        url = f"s3://covid-eo-data/xco2/xco2_15day_mean.{query.month}.tif"
    mean, median = get_zonal_stat(query.geojson, url)
    return dict(mean=mean, median=median)
