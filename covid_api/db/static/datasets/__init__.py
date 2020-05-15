""" covid_api static datasets """
import os
from typing import List

from covid_api.models.static import Datasets, Dataset
data_dir = os.path.join(os.path.dirname(__file__))

class InvalidIdentifier(Exception):
    """Raise if no key is found"""

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

    def get(self, identifier: str) -> Dataset:
        """Fetch a Dataset."""
        try:
            return self._data[identifier]
        except KeyError:
            raise InvalidIdentifier(f"Invalid identifier: {identifier}")

    def get_all(self) -> Datasets:
        """Fetch all Datasets."""
        return Datasets(
            datasets=[dataset.dict() for dataset in self._data.values()]
        )

    def list(self) -> List[str]:
        """List all datasets"""
        return list(self._data.keys())

datasets = DatasetManager()
