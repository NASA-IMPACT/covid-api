from fastapi import APIRouter
from glob import glob

from covid_api.core import config
from covid_api.models.static import Dataset, Datasets
from covid_api.db.static.datasets import datasets

router = APIRouter()

@router.get(
    "/datasets",
    responses={200: dict(description="return a list of all available datasets")},
    response_model=Datasets,
)
def get_datasets():
   return datasets.get_all()

@router.get(
    "/datasets/{id}",
    responses={200: dict(description="return a dataset")},
    response_model=Dataset,
)
def get_dataset(id: str):
    return datasets.get(id)

