from fastapi import APIRouter
from glob import glob
import json

from covid_api.core import config
from covid_api.models.static import Detection
from covid_api.db.utils import s3_get

router = APIRouter()

@router.get(
    "/datasets/{type}/{site}/{date}.geojson",
    responses={200: dict(description="return a detection geojson")},
    response_model=Detection,
)
def get_dataset(type: str, site: str, date: str):
    return json.loads(s3_get(
        bucket=config.INDICATOR_BUCKET,
        key=f"detections/{type}/{site}/{date}.geojson",
        ))

