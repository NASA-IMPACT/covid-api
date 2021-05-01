"""Static models."""

from typing import Any, List, Optional, Union

from geojson_pydantic.geometries import Polygon
from pydantic import BaseModel  # , validator

# from pydantic.color import Color


def to_camel(snake_str: str) -> str:
    """
    Converts snake_case_string to camelCaseString
    """
    first, *others = snake_str.split("_")
    return "".join([first.lower(), *map(str.title, others)])


class Source(BaseModel):
    """Base Source Model"""

    type: str


class NonGeoJsonSource(Source):
    """Source Model for all non-geojson data types"""

    tiles: List[str]


class GeoJsonSource(Source):
    """Source Model for geojson data types"""

    data: str


class Swatch(BaseModel):
    """Swatch Model."""

    color: str
    name: str


class LabelStop(BaseModel):
    """Model for Legend stops with color + label"""

    color: str
    label: str


class Legend(BaseModel):
    """Legend Model."""

    type: str
    min: Optional[str]
    max: Optional[str]
    stops: Union[List[str], List[LabelStop]]


class DatasetComparison(BaseModel):
    """ Dataset `compare` Model."""

    enabled: bool
    help: str
    year_diff: int
    map_label: str
    source: NonGeoJsonSource
    time_unit: Optional[str]


def snake_case_to_kebab_case(s):
    """Util method to convert kebab-case fieldnames to snake_case."""
    return s.replace("_", "-")


class Paint(BaseModel):
    """Paint Model."""

    raster_opacity: float

    class Config:
        """Paint Model Config"""

        alias_generator = snake_case_to_kebab_case
        allow_population_by_field_name = True


class Dataset(BaseModel):
    """Dataset Model."""

    id: str
    name: str
    type: str
    is_periodic: bool = False
    time_unit: Optional[str] = ""
    domain: Optional[List[str]] = []
    source: Union[NonGeoJsonSource, GeoJsonSource]
    background_source: Optional[Union[NonGeoJsonSource, GeoJsonSource]]
    exclusive_with: Optional[List[str]] = []
    swatch: Optional[Swatch]
    compare: Optional[DatasetComparison]
    legend: Optional[Legend]
    paint: Optional[Paint]
    info: Optional[str] = ""


class DatasetExternal(Dataset):
    """ Public facing dataset model (uses camelCase fieldnames) """

    class Config:
        """Generates alias to convert all fieldnames from snake_case to camelCase"""

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
