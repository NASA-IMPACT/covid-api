from typing import List, Tuple, Dict
from pydantic import BaseModel

class Polygon(BaseModel):
    """
    Polygon structured as a geometry object of a GeoJSON feature.

    https://tools.ietf.org/html/rfc7946#section-3.1.6

    """

    type: str = "Polygon"
    coordinates: List[List[Tuple[float, float]]]

class Feature(BaseModel):
    type: str
    geometry: Polygon
    properties: Dict