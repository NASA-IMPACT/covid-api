"""Groups endpoint."""

from covid_api.db.static.groups import groups
from covid_api.models.static import IndicatorGroup, IndicatorGroups

from fastapi import APIRouter

router = APIRouter()


@router.get(
    "/indicator_groups",
    responses={
        200: dict(description="return a list of all available indicator groups")
    },
    response_model=IndicatorGroups,
)
def get_groups():
    """Return group list."""
    return groups.get_all()


@router.get(
    "/indicator_groups/{id}",
    responses={200: dict(description="return a group")},
    response_model=IndicatorGroup,
)
def get_group(id: str):
    """Return group info."""
    return groups.get(id)
