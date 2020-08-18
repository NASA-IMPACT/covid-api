""" covid_api static datasets """
import os
import re
from typing import List, Dict, Set, Any

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

    def get(self, spotlight_id: str) -> Datasets:
        """
        Fetches all the datasets avilable for a given spotlight. If the
        spotlight_id provided is "global" then this method will return
        all datasets that are NOT spotlight specific. Raises an
        `InvalidIdentifier` exception if the provided spotlight_id does
        not exist.
        """
        if spotlight_id == "global":

            spotlight_datasets = self.get_global_datasets()
            spotlight_datasets = self._overload_domain(datasets=spotlight_datasets)

            return Datasets(
                datasets=[dataset.dict() for dataset in spotlight_datasets.values()]
            )

        # Verify that the requested spotlight exists
        try:
            site = sites.get(spotlight_id)
        except InvalidIdentifier:
            raise

        if site.id in ["du", "gh"]:
            site.id = f"{site.id}|EUPorts"

        # find all "folders" in S3 containing keys for the given spotlight
        # each "folder" corresponds to a dataset
        spotlight_dataset_folders = get_dataset_folders_by_spotlight(
            spotlight_id=site.id
        )

        # filter the dataset items by those corresponding the folders above
        spotlight_datasets = self.filter_datasets_by_folders(
            folders=spotlight_dataset_folders
        )

        spotlight_datasets = self._overload_domain(
            datasets=spotlight_datasets, spotlight_id=site.id
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
        spotlight (Optional[dict]): spotlight to further precise `domain`
        search

        Returns:
        ------
        dict: the `datasets` object, with an updated `domain` value for each
        dataset in the `datasets` object.
        """

        for key, dataset in datasets.items():

            regexp = r"s3://covid-eo-data/(.*)/"

            if key in ["detections-plane", "detections-ship"]:
                regexp = r"/(detections/[^/]*)/"

            dataset_folder_search = re.search(regexp, dataset.source.tiles[0])

            if not dataset_folder_search:
                continue

            dataset_folder = dataset_folder_search.group(1)

            # if the dataset folder is for `detection-ships` or `detection-plane`
            # the returned regexp match will contain a `/` character that should
            # be replaced with a `-` character in order to find the correct
            # s3 folder
            if key in ["detections-plane", "detections-ship"]:
                dataset_folder = dataset_folder.replace("/", "-")

            domain_args: Dict[str, Any] = {"dataset_folder": dataset_folder}

            if dataset.time_unit:
                # if `time_unit` is present in the dataset metadata item, the
                # dataset is considered to be periodic and only the start and
                # end dates will be returned.
                domain_args["time_unit"] = dataset.time_unit

            if spotlight_id:
                domain_args["spotlight_id"] = spotlight_id

            dataset.domain = get_dataset_domain(**(domain_args))

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
        folders = {
            f.replace("-", "/") if f in ["detections-ship", "detections-plane"] else f
            for f in folders
        }

        return {
            k: v
            for k, v in self._data.items()
            if any(
                [
                    re.search(rf"/{folder}/", v.source.tiles[0], re.IGNORECASE,)
                    for folder in folders
                ]
            )
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
