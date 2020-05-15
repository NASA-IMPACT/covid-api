from typing import Dict, List
from pydantic import BaseModel
from pydantic.color import Color

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