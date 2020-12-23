"""API planet mosaic tiles."""
from functools import partial
from typing import Any, Dict

from rio_tiler.utils import render

from covid_api.api import utils
from covid_api.db.memcache import CacheLayer
from covid_api.ressources.common import mimetype
from covid_api.ressources.enums import ImageType
from covid_api.ressources.responses import TileResponse

from fastapi import APIRouter, Depends, Path, Query

from starlette.concurrency import run_in_threadpool

_render = partial(run_in_threadpool, render)
_tile = partial(run_in_threadpool, utils.modis_tile)

router = APIRouter()
responses = {
    200: {
        "content": {
            "image/png": {},
            "image/jpg": {},
            "image/webp": {},
            "image/tiff": {},
            "application/x-binary": {},
        },
        "description": "Return an image.",
    }
}
tile_routes_params: Dict[str, Any] = dict(
    responses=responses, tags=["modis"], response_class=TileResponse
)


@router.get(r"/modis/{z}/{x}/{y}", **tile_routes_params)
async def tile(
    z: int = Path(..., ge=0, le=30, description="Mercator tiles's zoom level"),
    x: int = Path(..., description="Mercator tiles's column"),
    y: int = Path(..., description="Mercator tiles's row"),
    date: str = Query(..., description="date of site for detections"),
    site: str = Query(..., description="id of site for detections"),
    cache_client: CacheLayer = Depends(utils.get_cache),
) -> TileResponse:
    """Handle /modis requests."""
    timings = []
    headers: Dict[str, str] = {}

    tile_hash = utils.get_hash(**dict(z=z, x=x, y=y, planet=False))

    content = None
    if cache_client:
        try:
            content, ext = cache_client.get_image_from_cache(tile_hash)
            headers["X-Cache"] = "HIT"
        except Exception:
            content = None

    if not content:
        with utils.Timer() as t:
            content = await _tile(x, y, z, date)

        timings.append(("Read", t.elapsed))
        timings.append(("Format", t.elapsed))

        if cache_client and content:
            cache_client.set_image_cache(tile_hash, (content, ImageType.png))

    if timings:
        headers["X-Server-Timings"] = "; ".join(
            ["{} - {:0.2f}".format(name, time * 1000) for (name, time) in timings]
        )

    return TileResponse(
        content, media_type=mimetype[ImageType.png.value], headers=headers
    )
