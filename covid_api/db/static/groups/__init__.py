""" covid_api indicator groups """
import os
from typing import List

from covid_api.models.static import IndicatorGroup, IndicatorGroups
from covid_api.db.static.errors import InvalidIdentifier

data_dir = os.path.join(os.path.dirname(__file__))


class GroupManager(object):
    """Default Group holder."""

    def __init__(self):
        """Load all groups in a dict."""
        groups = [
            os.path.splitext(f)[0] for f in os.listdir(data_dir) if f.endswith(".json")
        ]

        self._data = {
            group: IndicatorGroup.parse_file(os.path.join(data_dir, f"{group}.json"))
            for group in groups
        }

    def get(self, identifier: str) -> IndicatorGroup:
        """Fetch a Group."""
        try:
            return self._data[identifier]
        except KeyError:
            raise InvalidIdentifier(f"Invalid identifier: {identifier}")

    def get_all(self) -> IndicatorGroups:
        """Fetch all Groups."""
        return IndicatorGroups(groups=[group.dict() for group in self._data.values()])

    def list(self) -> List[str]:
        """List all groups"""
        return list(self._data.keys())


groups = GroupManager()
