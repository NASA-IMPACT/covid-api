from datetime import date as d
from typing import Dict, List, Tuple
from pydantic import BaseModel

class TimelapseValue(BaseModel):
    mean: float
    median: float

class Polygon(BaseModel):
    type: str = "Polygon"
    coordinates: List[List[Tuple[float, float]]]

class Feature(BaseModel):
    type: str
    geometry: Polygon
    properties: Dict

class TimelapseRequest(BaseModel):
    month: str
    geojson: Feature