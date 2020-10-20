"""Static models."""

from typing import Any, Dict, List, Optional, Union

from geojson_pydantic.features import FeatureCollection
from geojson_pydantic.geometries import Polygon
from pydantic import BaseModel
from pydantic.color import Color


def to_camel(snake_str):
    first, *others = snake_str.split("_")
    return "".join([first.lower(), *map(str.title, others)])


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
    min: Optional[str]
    max: Optional[str]
    stops: Union[List[Color], List[Dict[str, str]]]


class Dataset(BaseModel):
    """Dataset Model."""

    id: str
    name: str
    description: str = ""
    type: str
    is_periodic: bool = True
    time_unit: str
    domain: List = []
    source: Source
    background_source: Optional[Source]
    swatch: Swatch
    legend: Optional[Legend]
    info: str = ""


class DatasetExternal(Dataset):
    """ Public facing dataset model (uses camelCase fieldnames) """

    class Config:
        alias_generator = to_camel
        allow_population_by_field_name = True


class DatasetInternal(Dataset):
    """ Private dataset model (includes the dataset's location in s3) """

    s3_location: Optional[str]


class Datasets(BaseModel):
    """Dataset List Model."""

    datasets: List[DatasetExternal]


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
    prose: Optional[str]
    indicators: List[str]


class IndicatorGroups(BaseModel):
    """Indicator Group List Model."""

    groups: List[IndicatorGroup]


class Detection(FeatureCollection):
    """Detection Model"""

    pass
