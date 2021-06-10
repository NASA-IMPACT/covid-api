"""Tilelapse models."""

import re
from typing import List, Optional

from area import area
from geojson_pydantic.features import Feature
from geojson_pydantic.geometries import Polygon
from pydantic import BaseModel, validator

from covid_api.core import config


def to_camel(s):
    """Convert string s from `snake_case` to `camelCase`"""
    return re.sub(r"(?!^)_([a-zA-Z])", lambda m: m.group(1).upper(), s)


class PolygonFeature(Feature):
    """Feature model."""

    geometry: Polygon


class TimelapseValue(BaseModel):
    """"Timelapse values model."""

    mean: float
    median: float


class TimelapseRequest(BaseModel):
    """"Timelapse request model."""

    # TODO: parse date/date_range into a python `datetime` object (maybe using a validator? )
    # TODO: validate that exactly one of `date` or `date_range` is supplied
    date: Optional[str]
    date_range: Optional[List[str]]
    geojson: PolygonFeature
    dataset_id: str
    spotlight_id: Optional[str]

    @validator("geojson")
    def validate_query_area(cls, v, values):
        """Ensure that requested AOI is is not larger than 200 000 km^2, otherwise
        query takes too long"""
        if area(v.geometry.dict()) / (
            1000 * 1000
        ) > config.TIMELAPSE_MAX_AREA and values.get("date_range"):

            raise ValueError(
                "AOI cannot exceed 200 000 km^2, when queried with a date range. "
                "To query with this AOI please query with a single date"
            )
        return v

    @validator("date_range")
    def validate_date_objects(cls, v):

        """Validator"""
        if not len(v) == 2:
            raise ValueError("Field `dateRange` must contain exactly 2 dates")
        return v

    class Config:
        """Generate alias to convert `camelCase` requests to `snake_case` fields to be used
        within the code"""

        alias_generator = to_camel
