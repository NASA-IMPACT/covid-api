""" covid_api static sites """
import os
from typing import List
from enum import Enum

from covid_api.models.static import Site, Sites
from covid_api.db.static.errors import InvalidIdentifier

from covid_api.db.utils import get_indicators

data_dir = os.path.join(os.path.dirname(__file__))


class SiteManager(object):
    """Default Site holder."""

    def __init__(self):
        """Load all datasets in a dict."""
        site_ids = [
            os.path.splitext(f)[0] for f in os.listdir(data_dir) if f.endswith(".json")
        ]

        self._data = {
            site: Site.parse_file(os.path.join(data_dir, f"{site}.json"))
            for site in site_ids
        }

    def get(self, identifier: str) -> Site:
        """Fetch a Site."""
        try:
            site = self._data[identifier]
            site.indicators = get_indicators(identifier)
            return site
        except KeyError:
            raise InvalidIdentifier(f"Invalid identifier: {identifier}")

    def get_all(self) -> Sites:
        """Fetch all Sites."""
        return Sites(
            sites=[site.dict(exclude={"indicators"}) for site in self._data.values()]
        )

    def list(self) -> List[str]:
        """List all sites"""
        return list(self._data.keys())


sites = SiteManager()

SiteNames = Enum("SiteNames", [(site, site) for site in sites.list()])  # type: ignore
