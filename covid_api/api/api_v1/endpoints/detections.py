""" Machine Learning Detections. """
from fastapi import APIRouter, HTTPException
import json
from enum import Enum

from covid_api.core import config
from covid_api.models.static import Detection
from covid_api.db.utils import s3_get
from covid_api.db.static.sites import SiteNames

router = APIRouter()

# TODO: unhardcoded types and dates
MLTypes = Enum("MLTypes", [(ml, ml) for ml in ["ship", "multiple"]])  # type: ignore


@router.get(
    "/detections/{ml_type}/{site}/{date}.geojson",
    responses={
        200: dict(description="return a detection geojson"),
        404: dict(description="no detections found"),
    },
    response_model=Detection,
)
def get_detection(ml_type: MLTypes, site: SiteNames, date: str):
    """ Handle /detections requests."""
    try:
        return json.loads(
            s3_get(
                bucket=config.INDICATOR_BUCKET,
                key=f"detections/{ml_type.value}/{site.value}/{date}.geojson",
            )
        )
    except Exception:
        raise HTTPException(status_code=404, detail="Detections not found")
