""" covid_api static datasets """
import os
import re
from copy import deepcopy
from typing import Any, Dict, List, Set

from covid_api.db.static.errors import InvalidIdentifier
from covid_api.db.static.sites import sites
from covid_api.db.utils import get_dataset_domain, get_dataset_folders_by_spotlight
from covid_api.models.static import DatasetInternal, Datasets

data_dir = os.path.join(os.path.dirname(__file__))


class DatasetManager(object):
    """Default Dataset holder."""

    def __init__(self):
        """Load all datasets in a dict."""
        datasets = [
            os.path.splitext(f)[0] for f in os.listdir(data_dir) if f.endswith(".json")
        ]

        self._data = {
            dataset: DatasetInternal.parse_file(
                os.path.join(data_dir, f"{dataset}.json")
            )
            for dataset in datasets
        }

    def get(self, spotlight_id: str) -> Datasets:
        """
        Fetches all the datasets avilable for a given spotlight. If the
        spotlight_id provided is "global" then this method will return
        all datasets that are NOT spotlight specific. Raises an
        `InvalidIdentifier` exception if the provided spotlight_id does
        not exist.
        """
        global_datasets = self.get_global_datasets()
        global_datasets = self._overload_domain(datasets=global_datasets)

        if spotlight_id == "global":

            return Datasets(
                datasets=[
                    dataset.dict(exclude={"s3_location"})
                    for dataset in global_datasets.values()
                ]
            )

        # Verify that the requested spotlight exists
        try:
            site = sites.get(spotlight_id)
        except InvalidIdentifier:
            raise

        # Append "EUPorts" to the spotlight ID's if the requested spotlight id
        # was one of "du" or "gh", since certain datasets group both spotlights
        # under a single value: "EUPorts". It's then necessary to search,
        # and extract domain for each option ("du"/"gh" and "EUPorts") separately

        spotlight_ids = [site.id]
        if site.id in ["du", "gh"]:
            spotlight_ids.append("EUPorts")

        spotlight_datasets = {}

        for spotlight_id in spotlight_ids:
            # find all "folders" in S3 containing keys for the given spotlight
            # each "folder" corresponds to a dataset.
            spotlight_dataset_folders = get_dataset_folders_by_spotlight(
                spotlight_id=spotlight_id
            )
            # filter the dataset items by those corresponding the folders above
            # and add the datasets to the previously filtered `global` datasets
            datasets = self.filter_datasets_by_folders(
                folders=spotlight_dataset_folders
            )

            datasets = self._overload_spotlight_id(
                datasets=datasets, spotlight_id=spotlight_id
            )

            datasets = self._overload_domain(
                datasets=datasets, spotlight_id=spotlight_id
            )
            spotlight_datasets.update(datasets)

        if spotlight_id == "tk":
            spotlight_datasets["water-chlorophyll"].source.tiles = [
                tile.replace("&rescale=-100%2C100", "")
                for tile in spotlight_datasets["water-chlorophyll"].source.tiles
            ]

        # global datasets are returned for all spotlights
        spotlight_datasets.update(global_datasets)

        return Datasets(
            datasets=[
                dataset.dict(exclude={"s3_location"})
                for dataset in spotlight_datasets.values()
            ]
        )

    def get_all(self) -> Datasets:
        """Fetch all Datasets. Overload domain with S3 scanned domain"""
        self._data = self._overload_domain(datasets=self._data)
        return Datasets(
            datasets=[
                dataset.dict(exclude={"s3_location"}) for dataset in self._data.values()
            ]
        )

    def list(self) -> List[str]:
        """List all datasets"""
        return list(self._data.keys())

    @staticmethod
    def _overload_spotlight_id(datasets: dict, spotlight_id: str):
        """
        Returns the provided `datasets` objects with an updated value for
        each dataset's `source.tiles` and `background_source.tiles` keys.
        The string "{spotlightId}" in the `tiles` URL(s) is replaced with the
        actual value of the spotlightId (eg: "ny", "sf", "tk")
        Params:
        ------
        datasets (dict): dataset metadata objects for which to overload
        `source.tiles` and `background_source.tiles` keys.
        spotlight_id ([dict]): spotlight id value with which to replace
        "{spotlightId}"

        Returns:
        ------
        dict: the `datasets` object, with an updated `source.tiles` and
        `background_source.tiles` values for each dataset in the `datasets` object.
        """
        for _, dataset in datasets.items():
            dataset.source.tiles = [
                url.replace("{spotlightId}", spotlight_id)
                for url in dataset.source.tiles
            ]

            if not dataset.background_source:
                continue

            dataset.background_source.tiles = [
                url.replace("{spotlightId}", spotlight_id)
                for url in dataset.background_source.tiles
            ]
        return datasets

    @staticmethod
    def _overload_domain(datasets: dict, spotlight_id: str = None):
        """
        Returns the provided `datasets` object with an updated value for
        each dataset's `domain` key.
        The domain is extracted by listing keys in S3 belonging to that
        dataset (and spotlight, if provided) and extracting the dates from
        those keys.

        Params:
        ------
        datasets (dict): dataset metadata objects for which to overload
        `domain` keys.
        spotlight_id (Optional[str]): spotlight_id to further precise `domain`
        search

        Returns:
        ------
        dict: the `datasets` object, with an updated `domain` value for each
        dataset in the `datasets` object.
        """

        for _, dataset in datasets.items():

            # No point in searching for files in S3 if the dataset isn't stored there!
            if not dataset.s3_location:
                continue

            domain_args: Dict[str, Any] = {
                "dataset_folder": dataset.s3_location,
                "is_periodic": dataset.is_periodic,
            }

            if spotlight_id:
                domain_args["spotlight_id"] = spotlight_id

            dataset.domain = get_dataset_domain(**domain_args)

        return datasets

    def filter_datasets_by_folders(self, folders: Set[str]) -> Dict:
        """
        Returns all datasets corresponding to a set of folders (eg: for
        folders {"BMHD_30M_MONTHLY", "xco2"} this method would return the
        "Nightlights HD" and the "CO2" dataset metadata objects)

        Params:
        -------
        folders (Set[str]): folders to filter datasets

        Returns:
        --------
        Dict : Metadata objects for the datasets corresponding to the
            folders provided.
        """
        # deepcopy is necessary because the spotlight and domain overriding was
        # affecting the original dataset metadata items and returning the same values
        # in subsequent API requests for different spotlights
        return {
            k: v for k, v in deepcopy(self._data).items() if v.s3_location in folders
        }

    def get_global_datasets(self):
        """
        Returns all datasets which do not reference a specific spotlight, by
        filtering out datasets where the "source.tiles" value contains either
        `spotlightId`.
        """
        return {
            k: v
            for k, v in self._data.items()
            if not re.search(r"{spotlightId}", v.source.tiles[0])
        }


datasets = DatasetManager()
