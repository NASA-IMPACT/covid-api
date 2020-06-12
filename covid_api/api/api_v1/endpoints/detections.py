""" Machine Learning Detections. """
from fastapi import APIRouter
import json
from enum import Enum

from covid_api.core import config
from covid_api.models.static import Detection
from covid_api.db.utils import s3_get
from covid_api.db.static.sites import SiteNames

router = APIRouter()

# TODO: unhardcoded types and dates
MLTypes = Enum("MLTypes", [(ml, ml) for ml in ["ship", "multiple"]])  # type: ignore
Dates = Enum("Dates", [(d, d) for d in ["2020_03_11"]])  # type: ignore


@router.get(
    "/detections/{ml_type}/{site}/{date}.geojson",
    responses={200: dict(description="return a detection geojson")},
    response_model=Detection,
)
def get_detection(ml_type: MLTypes, site: SiteNames, date: Dates):
    """ Handle /detections requests."""
    print(ml_type, site, date)
    return json.loads(
        s3_get(
            bucket=config.INDICATOR_BUCKET,
            key=f"detections/{ml_type.value}/{site.value}/{date.value}.geojson",
        )
    )
