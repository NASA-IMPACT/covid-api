""" covid_api static datasets """
import json
import os
from typing import List

import botocore

from covid_api.core.config import (
    DATASET_METADATA_FILENAME,
    DATASET_METADATA_GENERATOR_FUNCTION_NAME,
    INDICATOR_BUCKET,
)
from covid_api.db.static.errors import InvalidIdentifier
from covid_api.db.static.sites import sites
from covid_api.db.utils import invoke_lambda, s3_get
from covid_api.models.static import DatasetInternal, Datasets, GeoJsonSource

data_dir = os.path.join(os.path.dirname(__file__))

class DatasetManager(object):
    """Default Dataset holder."""

    def __init__(self):
        """Load all datasets in a dict."""

        pass

    def _data(self):
        static_dataset_files = [
            os.path.splitext(f)[0] for f in os.listdir(data_dir) if f.endswith(".json")
        ]
        static_datasets = {
            dataset: DatasetInternal.parse_file(
                os.path.join(data_dir, f"{dataset}.json")
            )
            for dataset in static_dataset_files
        }
        remote_datasets = self._load_remote_metadata()
        return remote_datasets.update(static_datasets)


    def _load_remote_metadata(self):
        try:
            if os.environ.get('RUN_LOCAL') == 'true':
                with open(DATASET_METADATA_FILENAME, 'r') as datasets_json:
                    return json.loads(datasets_json.read())
            else:
                return json.loads(
                    s3_get(bucket=INDICATOR_BUCKET, key=DATASET_METADATA_FILENAME)
                )
        except botocore.errorfactory.ClientError as e:

            if e.response["Error"]["Code"] == "NoSuchKey":
                print(
                    "No datasets domain metadata file found, requesting generation"
                    " of a new file. This may take several minutes."
                )
                # invoke_lambda should return the output of the lambda's execution
                # however there are issues with accessing the output object within the
                # "Payload" returned by the lambda_invocation (see docstring).
                # Instead the thread is held while the lambda executes and then
                # loads the metadata from s3.

                invoke_lambda(
                    lambda_function_name=DATASET_METADATA_GENERATOR_FUNCTION_NAME
                )
                return json.loads(
                    s3_get(bucket=INDICATOR_BUCKET, key=DATASET_METADATA_FILENAME)
                )

    def get(self, spotlight_id: str, api_url: str) -> Datasets:
        """
        Fetches all the datasets avilable for a given spotlight. If the
        spotlight_id provided is "global" then this method will return
        all datasets that are NOT spotlight specific. Raises an
        `InvalidIdentifier` exception if the provided spotlight_id does
        not exist.

        Params:
        -------
        spotlight_id (str): spotlight id to return datasets for
        api_url(str): {scheme}://{host} of request originator in order
            to return correctly formated source urls

        Returns:
        -------
        (Datasets) pydantic model contains a list of datasets' metadata
        """

        global_datasets = self._process(
            self._load_remote_metadata()["global"],
            api_url=api_url,
            spotlight_id="global",
        )

        if spotlight_id == "global":
            return Datasets(datasets=[dataset for dataset in global_datasets.values()])

        # Verify that the requested spotlight exists
        try:
            site = sites.get(spotlight_id)
        except InvalidIdentifier:
            raise

        # spotlight_datasets = self._process(
        #     self._load_remote_metadata()[site.id],
        #     api_url=api_url,
        #     spotlight_id=site.id,
        # )

        return Datasets(
            datasets=[
                dataset for dataset in [*global_datasets.values()]#, *spotlight_datasets]
            ]
        )

    def get_all(self, api_url: str) -> Datasets:
        """Fetch all Datasets. Overload domain with S3 scanned domain"""
        # print(self._load_remote_metadata())
        # datasets = self._process(
        #     datasets_domains_metadata=self._load_remote_metadata()["_all"],
        #     api_url=api_url,
        # )
        datasets = self._load_remote_metadata()['_all']
        return Datasets(datasets=[dataset for dataset in datasets.values()])

    def list(self) -> List[str]:
        """List all datasets"""
        return list(self._data().keys())

    def _format_urls(self, tiles: List[str], api_url: str, spotlight_id: str = None):
        if spotlight_id:
            return [
                tile.replace("{api_url}", api_url).replace(
                    "{spotlightId}", spotlight_id
                )
                for tile in tiles
            ]
        return [tile.replace("{api_url}", api_url) for tile in tiles]

    def _process(
        self, datasets_domains_metadata: dict, api_url: str, spotlight_id: str = None
    ):
        """
        Processes datasets to be returned to the API consumer:
        - Updates dataset domains for all returned datasets
        - Inserts api url into source urls
        - Inserts spotlight id into source url (if a spotlight id is provided)

        Params:
        -------
        output_datasets (dict): Dataset domains for the datasets to be returned.
        api_url (str):
            Base url, of the form {schema}://{host}, extracted from the request, to
            prepend all tile source urls with.
        spotlight_id (Optional[str]):
            Spotlight ID (if requested), to be inserted into the source urls

        Returns:
        --------
        (list) : datasets metadata objects (to be serialized as a pydantic Datasets
            model)
        """
        output_datasets = {
            k: v
            for k, v in self._data().items()
            if k in datasets_domains_metadata.keys()
        }

        for k, dataset in output_datasets.items():

            # overload domain with domain returned from s3 file
            dataset.domain = datasets_domains_metadata[k]["domain"]

            # format url to contain the correct API host and
            # spotlight id (if a spotlight was requested)
            format_url_params = dict(api_url=api_url)
            if spotlight_id:
                if k == "nightlights-viirs" and spotlight_id in ["du", "gh"]:
                    spotlight_id = "EUPorts"
                format_url_params.update(dict(spotlight_id=spotlight_id))

            dataset.source.tiles = self._format_urls(
                tiles=dataset.source.tiles, **format_url_params
            )
            if 'background_source' in dataset and dataset.background_source:
                dataset.background_source.tiles = self._format_urls(
                    tiles=dataset.background_source.tiles, **format_url_params
                )
            if 'compare' in dataset and dataset.compare:
                dataset.compare.source.tiles = self._format_urls(
                    tiles=dataset.compare.source.tiles, **format_url_params
                )
            # source URLs of background tiles for `detections-*` datasets are
            # handled differently in the front end so the the `source` objects
            # get updated here
            if k.startswith("detections-"):
                dataset.source = GeoJsonSource(
                    type=dataset.source.type, data=dataset.source.tiles[0]
                ).dict()

            if spotlight_id == "tk" and k == "water-chlorophyll":
                dataset.source.tiles = [
                    tile.replace("&rescale=-100%2C100", "")
                    for tile in dataset.source.tiles
                ]

        return output_datasets.values()


datasets = DatasetManager()
