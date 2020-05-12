"""API metadata."""

from typing import Any, Dict, Optional, Union

import os
import re
from functools import partial
from urllib.parse import urlencode

import numpy

from rio_tiler.io import cogeo

from fastapi import APIRouter, Query
from starlette.requests import Request
from starlette.responses import Response

from covid_api.core import config
from covid_api.models.timelapse import Timelapse, TimelapseRequest

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
    tv = dict(date="2020-01-01", value=42)
    temp = dict(values=[tv])
    print(temp)
    return temp



