from fastapi import APIRouter
from glob import glob

from covid_api.core import config
from covid_api.models.static import IndicatorGroup, IndicatorGroups
from covid_api.db.static.groups import groups

router = APIRouter()

@router.get(
    "/indicator_groups",
    responses={200: dict(description="return a list of all available indicator groups")},
    response_model=IndicatorGroups,
)
def get_groups():
   return groups.get_all()

@router.get(
    "/indicator_groups/{id}",
    responses={200: dict(description="return a group")},
    response_model=IndicatorGroup,
)
def get_groups(id: str):
    return groups.get(id)
