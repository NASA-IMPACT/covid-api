
from typing import Dict, List, Union, Any, Optional, Tuple
from pydantic import BaseModel
from pydantic.color import Color
# from geojson_pydantic.geometries import Polygon

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

class Polygon(BaseModel):
    type: str = "Polygon"
    coordinates: List[List[Tuple[float, float]]]

class Site(BaseModel):
    id: str
    label: str
    center: List[float]
    polygon: Union[Polygon, None] = None
    bounding_box: Union[List[float], None] = None
    indicators: List[Any] = []

class Sites(BaseModel):
    sites: List[Site]

class IndicatorObservation(BaseModel):
    indicator: float
    indicator_conf_low: Optional[float] = None
    indicator_conf_high: Optional[float] = None
    baseline: Optional[float] = None
    baseline_conf_low: Optional[float] = None
    baseline_conf_high: Union[float, None] = None
    anomaly: Optional[str] = None

class IndicatorGroup(BaseModel):
    id: str
    label: str
    prose: str
    indicators: List[str]

class IndicatorGroups(BaseModel):
    groups: List[IndicatorGroup]