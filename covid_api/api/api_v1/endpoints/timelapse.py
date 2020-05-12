"""API metadata."""

from typing import Any, Dict, Optional, Union

from datetime import datetime, timedelta
import os
import re
from functools import partial
from urllib.parse import urlencode

import numpy as np

from rio_tiler.io import cogeo

from fastapi import APIRouter, Query
from starlette.requests import Request
from starlette.responses import Response

from covid_api.core import config
from covid_api.models.timelapse import Timelapse, TimelapseRequest
from covid_api.api.utils import get_zonal_stat

router = APIRouter()

@router.post(
    "/timelapse",
    responses={200: {"description": "Return timelapse values for a given geometry"}},
    response_model=Timelapse
)
def timelapse(
    query: TimelapseRequest,
    response: Response,
):
    """Handle /timelapse requests."""
    dates = np.arange(
        query.date_range[0],
        query.date_range[1] + timedelta(days=1),
        timedelta(days=1)
    ).astype(datetime)

    values = list()
    file_name = 's3://covid-eo-data/OMNO2d_HRD/{d}_NO2TropCS30_Col3_V4.hdf5.cog.tif'
    for date in dates:
        f_date = date.strftime('%Y_%m_%d')
        url = file_name.format(d=f_date)
        value = get_zonal_stat(query.geojson, url)
        values.append(dict(value=value, date=date))

    return dict(values=values)



