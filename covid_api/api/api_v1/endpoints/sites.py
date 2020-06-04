from fastapi import APIRouter
from glob import glob

from covid_api.core import config
from covid_api.models.static import Sites, Site
from covid_api.db.static.sites import sites

router = APIRouter()

@router.get(
    "/sites",
    responses={200: dict(description="return a list of all available sites")},
    response_model=Sites,
)
def get_sites():
   return sites.get_all()

@router.get(
    "/sites/{id}",
    responses={200: dict(description="return a site")},
    response_model=Site,
)
def get_site(id: str):
    return sites.get(id)
