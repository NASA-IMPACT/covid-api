from datetime import date as d
from typing import Dict, List, Tuple
from pydantic import BaseModel
from geojson_pydantic.features import Feature
from geojson_pydantic.geometries import Polygon

class PolygonFeature(Feature):
    geometry: Polygon

class TimelapseValue(BaseModel):
    mean: float
    median: float

class TimelapseRequest(BaseModel):
    month: str
    geojson: PolygonFeature