""" covid_api static datasets """
import os
import re
from typing import List

from covid_api.models.static import Datasets, Dataset
from covid_api.db.static.errors import InvalidIdentifier

from covid_api.db.static.sites import sites

from covid_api.db.utils import get_dataset_folders_by_spotlight, get_dataset_domain

data_dir = os.path.join(os.path.dirname(__file__))


class DatasetManager(object):
    """Default Dataset holder."""

    def __init__(self):
        """Load all datasets in a dict."""
        datasets = [
            os.path.splitext(f)[0] for f in os.listdir(data_dir) if f.endswith(".json")
        ]

        self._data = {
            dataset: Dataset.parse_file(os.path.join(data_dir, f"{dataset}.json"))
            for dataset in datasets
        }

        # loop through returned datasets, overloading "domain" with 
        # data extracted from S3, if an accessible S3 folder is present 
        # (not the case for population data)
        for _, dataset in self._data.items():

            if (dataset_folder := re.search(
                    "s3://covid-eo-data/(.*)/", dataset.source.tiles[0]
            )):
                domain_args = [dataset_folder.group(1)]
                if dataset.time_unit:
                    domain_args.append(dataset.time_unit)

                dataset.domain = get_dataset_domain(*tuple(domain_args))

    def get(self, spotlight_id: str) -> Datasets:
        """Fetches all the datasets avilable for a given Spotlight."""

        try:
            # Fetch site corresponding to the spotlight ID
            site = sites.get(spotlight_id)

            # Extracts datasets folders that contain keys for the given spotlight
            dataset_folders = get_dataset_folders_by_spotlight(site.id, site.label)

            # filter for datasets corresponding to the above folders
            self._data = {
                k: v
                for k, v in self._data.items()
                if any(
                    [
                        re.search(
                            rf"s3://covid-eo-data/{folder}/",
                            v.source.tiles[0],
                            re.IGNORECASE,
                        )
                        for folder in dataset_folders
                    ]
                )
            }
            return self.get_all()

        except InvalidIdentifier:
            raise InvalidIdentifier(f"Invalid identifier: {spotlight_id}")

    def get_all(self) -> Datasets:
        """Fetch all Datasets."""
        return Datasets(datasets=[dataset.dict() for dataset in self._data.values()])

    def list(self) -> List[str]:
        """List all datasets"""
        return list(self._data.keys())


datasets = DatasetManager()
