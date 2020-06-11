"""Static models."""

from typing import List, Any, Optional
from pydantic import BaseModel
from pydantic.color import Color
from geojson_pydantic.features import FeatureCollection
from geojson_pydantic.geometries import Polygon


class Source(BaseModel):
    """Source Model."""

    type: str
    tiles: List


class Swatch(BaseModel):
    """Swatch Model."""

    color: Color
    name: str


class Legend(BaseModel):
    """Legend Model."""

    type: str
    min: str
    max: str
    stops: List[Color]


class Dataset(BaseModel):
    """Dataset Model."""

    id: str
    name: str
    description: str = ""
    type: str
    domain: List = []
    source: Source
    swatch: Swatch
    legend: Legend
    info: str = ""


class Datasets(BaseModel):
    """Dataset List Model."""

    datasets: List[Dataset]


class Site(BaseModel):
    """Site Model."""

    id: str
    label: str
    center: List[float]
    polygon: Optional[Polygon] = None
    bounding_box: Optional[List[float]] = None
    indicators: List[Any] = []


class Sites(BaseModel):
    """Site List Model."""

    sites: List[Site]


class IndicatorObservation(BaseModel):
    """Indicator Observation Model."""

    indicator: float
    indicator_conf_low: Optional[float] = None
    indicator_conf_high: Optional[float] = None
    baseline: Optional[float] = None
    baseline_conf_low: Optional[float] = None
    baseline_conf_high: Optional[float] = None
    anomaly: Optional[str] = None


class IndicatorGroup(BaseModel):
    """Indicator Group Model."""

    id: str
    label: str
    prose: str
    indicators: List[str]


class IndicatorGroups(BaseModel):
    """Indicator Group List Model."""

    groups: List[IndicatorGroup]


class Detection(FeatureCollection):
    """Detection Model"""

    pass
