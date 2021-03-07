"""API metadata."""

import datetime

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
    landsat_stac_api = 'https://eod-catalog-svc-prod.astraea.earth/search?collection=landsat8_l1tp'
    # translate query date time to compliant date format
    # create bounding box from request or post polygon
    print(query.geojson.geometry.coordinates)
    coordinates = query.geojson.geometry.coordinates[0]
    bbox_coordinates = map(str, [coordinates[0][0], coordinates[0][1], coordinates[1][0], coordinates[2][1]])
    bbox = ','.join(bbox_coordinates)
    datetime_string = query.month
    datetime_obj = datetime.datetime.strptime(datetime_string, '%Y.%m.%d')
    landsat_stac_api_search = f"{landsat_stac_api}&bbox={bbox}&datetime={datetime_obj.isoformat()}Z"
    print(landsat_stac_api_search)
    if query.type == "modis-vi":
        url = f"s3://modis-vi-nasa/MOD13A1.006/{query.month}.tif"
    else:
        url = f"s3://covid-eo-data/xco2-mean/xco2_16day_mean.{query.month}.tif"
    mean, median = get_zonal_stat(query.geojson, url)
    return dict(mean=mean, median=median)
