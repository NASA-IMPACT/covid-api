from typing import List, Tuple, Dict
from pydantic import BaseModel

class Polygon(BaseModel):
    type: str = "Polygon"
    coordinates: List[List[Tuple[float, float]]]

class Feature(BaseModel):
    type: str
    geometry: Polygon
    properties: Dict