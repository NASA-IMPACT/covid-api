"""Tilelapse models."""

from geojson_pydantic.features import Feature
from geojson_pydantic.geometries import Polygon
from pydantic import BaseModel


class PolygonFeature(Feature):
    """Feature model."""

    geometry: Polygon


class TimelapseValue(BaseModel):
    """"Timelapse values model."""

    mean: float
    median: float


class TimelapseRequest(BaseModel):
    """"Timelapse request model."""

    month: str
    geojson: PolygonFeature
    type: str
