from datetime import date as d
from typing import Dict, List, Tuple
from pydantic import BaseModel

from .common import Feature

class TimelapseValue(BaseModel):
    mean: float
    median: float

class TimelapseRequest(BaseModel):
    month: str
    geojson: Feature