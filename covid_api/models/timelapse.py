"""Tilelapse models."""
import re
from typing import Optional

from geojson_pydantic.features import Feature
from geojson_pydantic.geometries import Polygon
from pydantic import BaseModel


def to_camel(s):
    """ Convert string s from `snake_case` to `camelCase` """
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

    date: str
    geojson: PolygonFeature
    dataset_id: str
    spotlight_id: Optional[str]

    class Config:
        """Generate alias to convert `camelCase` requests to `snake_case` fields to be used
        within the code """

        alias_generator = to_camel
