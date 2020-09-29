""" covid_api static datasets """
import os
import re
from typing import List, Dict, Set, Any

from covid_api.models.static import Datasets, Dataset
from covid_api.db.static.errors import InvalidIdentifier

from covid_api.db.static.sites import sites

from covid_api.db.utils import s3_get, get_dataset_folders_by_spotlight, get_dataset_domain
import boto3
import json
s3 = boto3.client("s3")

data_dir = os.path.join(os.path.dirname(__file__))
from covid_api.core.config import BUCKET, DATA_DIR

class DatasetManager(object):
    """Default Dataset holder."""

    def __init__(self):
        """Load all datasets in a dict."""
        list_objects_args = {
            "Bucket": BUCKET,
            "Prefix": f"{DATA_DIR}/collections/"
        }
        dataset_files = s3.list_objects_v2(**list_objects_args)['Contents']
        datasets = {}
        for file in dataset_files:
            if file.get('Size') > 0:
                key = file.get('Key')
                dataset_json = s3_get(bucket=BUCKET, key=file.get('Key'))
                dataset_name = key.split('/')[-1].replace('.json', '')
                datasets[dataset_name] = json.loads(dataset_json)
        # print(json.dumps(datasets, indent=2))
        self._data = datasets

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
                datasets=[dataset.dict() for dataset in global_datasets.values()]
            )

        # Verify that the requested spotlight exists
        try:
            site = sites.get(spotlight_id)
        except InvalidIdentifier:
            raise

        # Append EUPorts to the spotlight ID using a pipe character so that
        # the regexp will filter for either value, since certain datasets
        # contain data for both the `du` and `gh` spotlights under `EUPorts`
        if site.id in ["du", "gh"]:
            site.id = f"{site.id}|EUPorts"

        # find all "folders" in S3 containing keys for the given spotlight
        # each "folder" corresponds to a dataset.
        spotlight_dataset_folders = get_dataset_folders_by_spotlight(
            spotlight_id=site.id
        )

        # filter the dataset items by those corresponding the folders above
        # and add the datasets to the previously filtered `global` datasets
        spotlight_datasets = self.filter_datasets_by_folders(
            folders=spotlight_dataset_folders
        )
        spotlight_datasets = self._overload_domain(
            datasets=spotlight_datasets, spotlight_id=site.id
        )

        # global datasets are returned for all spotlights
        spotlight_datasets.update(global_datasets)

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

        return {k: v for k, v in self._data.items() if v.s3_location in folders}

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
