"""Tilelapse models."""
import re
from typing import List, Optional

from geojson_pydantic.features import Feature
from geojson_pydantic.geometries import Polygon
from pydantic import BaseModel, validator


def to_camel(s):
    """Convert string s from `snake_case` to `camelCase`"""
    return re.sub(r"(?!^)_([a-zA-Z])", lambda m: m.group(1).upper(), s)


class PolygonFeature(Feature):
    """Feature model."""

    geometry: Polygon


class TimelapseValue(BaseModel):
    """ "Timelapse values model."""

    mean: Optional[float]
    median: Optional[float]
    date: Optional[str]
    error: Optional[str]


class TimelapseRequest(BaseModel):
    """ "Timelapse request model."""

    # TODO: parse this into a python `datetime` object (maybe using a validator? )
    # TODO: validate that exactly one of `date` or `date_range` is supplied
    date: Optional[str]
    date_range: Optional[List[str]]
    geojson: PolygonFeature
    dataset_id: str
    spotlight_id: Optional[str]

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
