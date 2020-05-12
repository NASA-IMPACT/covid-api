from datetime import date as d
from typing import Dict, List, Tuple
from pydantic import BaseModel

class TimelapseValue(BaseModel):
    date: d
    value: float

class Timelapse(BaseModel):
    values: List[TimelapseValue]

class Polygon(BaseModel):
    type: str = "Polygon"
    coordinates: List[List[Tuple[float, float]]]

class Feature(BaseModel):
    type: str
    geometry: Polygon
    properties: Dict

class TimelapseRequest(BaseModel):
    date_range: Tuple[d, d]
    geojson: Feature