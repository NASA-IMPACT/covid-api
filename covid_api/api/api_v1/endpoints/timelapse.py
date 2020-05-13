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
from covid_api.models.timelapse import TimelapseValue, TimelapseRequest
from covid_api.api.utils import get_zonal_stat

router = APIRouter()

@router.post(
    "/timelapse",
    responses={200: {"description": "Return timelapse values for a given geometry"}},
    response_model=TimelapseValue
)
def timelapse(
    query: TimelapseRequest,
    response: Response,
):
    """Handle /timelapse requests."""
    url = f's3://covid-eo-data/OMNO2d_HRM/OMI_trno2_0.10x0.10_{query.month}_Col3_V4.nc.tif'
    value = get_zonal_stat(query.geojson, url)
    return dict(value=value)
