from typing import Dict, List, Union
from pydantic import BaseModel
from pydantic.color import Color
from geojson_pydantic.geometries import Polygon

class Source(BaseModel):
    type: str
    tiles: List

class Swatch(BaseModel):
    color: Color
    name: str

class Legend(BaseModel):
    type: str
    min: str
    max: str
    stops: List[Color]

class Dataset(BaseModel):
    id: str
    name: str
    description: str = ''
    type: str
    domain: List = []
    source: Source
    swatch: Swatch
    legend: Legend
    info: str = ''

class Datasets(BaseModel):
    datasets: List[Dataset]

class Site(BaseModel):
    id: str
    label: str
    center: List[float]
    polygon: Union[Polygon, None] = None
    bounding_box: Union[List[float], None] = None

class Sites(BaseModel):
    sites: List[Site]