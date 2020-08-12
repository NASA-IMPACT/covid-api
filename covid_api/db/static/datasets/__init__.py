""" covid_api static datasets """
import os
import re
from typing import List, Optional, Dict, Set, Any

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

    @staticmethod
    def _overload_domain(datasets: dict, spotlight: Optional[dict] = None):
        """Loop through returned datasets, overloading "domain" key with
        data extracted from S3, if an accessible S3 folder is present
        (not the case for population data)"""
        for _, dataset in datasets.items():

            dataset_folder = re.search(
                "s3://covid-eo-data/(.*)/", dataset.source.tiles[0]
            )

            if not dataset_folder:
                continue
            domain_args: Dict[str, Any] = dict(dataset_folder=dataset_folder.group(1))

            if dataset.time_unit:
                domain_args["time_unit"] = dataset.time_unit

            if spotlight:
                domain_args["spotlight"] = spotlight

            dataset.domain = get_dataset_domain(**(domain_args))
        return datasets

    def filter_datasets_by_folders(self, folders: Set[str]) -> Dict:
        """
        Returns all datasets corresponding to a set of folders.

        Params:
        -------
        folders (Set[str]): folder's to filter datasets by (eg:
            for folders {"BMHD_30M_MONTHLY", "xco2"} this method
            would return the "Nightlights HD" and the CO2 datasets)

        Returns:
        --------
        Dict : Metadata objects for the datasets corresponding to the
            folders provided.
        """
        return {
            k: v
            for k, v in self._data.items()
            if any(
                [
                    re.search(
                        rf"s3://covid-eo-data/{folder}/",
                        v.source.tiles[0],
                        re.IGNORECASE,
                    )
                    for folder in folders
                ]
            )
        }

    def get_global_datasets(self):
        """
        Returns all datasets which do not reference a specific spotlight
        """
        return {
            k: v
            for k, v in self._data.items()
            if not re.search(r"{spotlightId}|{spotlightName}", v.source.tiles[0])
        }

    def get(self, spotlight_id: str) -> Datasets:
        """Fetches all the datasets avilable for a given Spotlight."""

        if spotlight_id == "global":
            spotlight_datasets = self.get_global_datasets()

            spotlight_datasets = self._overload_domain(datasets=spotlight_datasets)
            return Datasets(
                datasets=[dataset.dict() for dataset in spotlight_datasets.values()]
            )

        try:
            # Fetch site corresponding to the spotlight ID
            site = sites.get(spotlight_id)
        except InvalidIdentifier:
            raise

        spotlight_dataset_folders = get_dataset_folders_by_spotlight(
            site.id, site.label
        )

        spotlight_datasets = self.filter_datasets_by_folders(spotlight_dataset_folders)

        spotlight_datasets = self._overload_domain(
            datasets=spotlight_datasets,
            spotlight={"spotlight_id": site.id, "spotlight_name": site.label},
        )

        return Datasets(
            datasets=[dataset.dict() for dataset in spotlight_datasets.values()]
        )

    def get_all(self) -> Datasets:
        """Fetch all Datasets. Overload domain with S3 scanned domain"""
        self._data = self._overload_domain(datasets=self._data)
        return Datasets(datasets=[dataset.dict() for dataset in self._data.values()])

    def list(self) -> List[str]:
        """List all datasets"""
        return list(self._data.keys())


datasets = DatasetManager()
