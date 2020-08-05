"""API planet mosaic tiles."""

from typing import Any, Dict, Union, Optional

import re

from functools import partial

import numpy as np
import requests

from fastapi import APIRouter, Depends, Query, Path
from starlette.concurrency import run_in_threadpool

from rio_tiler.profiles import img_profiles
from rio_tiler.utils import render

from covid_api.api import utils
from covid_api.db.memcache import CacheLayer
from covid_api.ressources.enums import ImageType
from covid_api.ressources.common import drivers, mimetype
from covid_api.ressources.responses import TileResponse


_render = partial(run_in_threadpool, render)
_tile = partial(run_in_threadpool, utils.planet_mosaic_tile)

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
    responses=responses, tags=["planet"], response_class=TileResponse
)


@router.get(r"/planet/{z}/{x}/{y}", **tile_routes_params)
async def tile(
    z: int = Path(..., ge=0, le=30, description="Mercator tiles's zoom level"),
    x: int = Path(..., description="Mercator tiles's column"),
    y: int = Path(..., description="Mercator tiles's row"),
    scenes: str = Query(..., description="Comma separated Planets scenes to mosaic."),
    cache_client: CacheLayer = Depends(utils.get_cache),
) -> TileResponse:
    """Handle /planet requests."""
    timings = []
    headers: Dict[str, str] = {}

    tile_hash = utils.get_hash(**dict(z=z, x=x, y=y, scenes=scenes,))

    content = None
    if cache_client:
        try:
            content, ext = cache_client.get_image_from_cache(tile_hash)
            headers["X-Cache"] = "HIT"
        except Exception:
            content = None

    if not content:
        with utils.Timer() as t:
            tile, mask = await _tile(scenes, x, y, z)
        timings.append(("Read", t.elapsed))

        content = await _render(tile, mask)

        timings.append(("Format", t.elapsed))

        if cache_client and content:
            cache_client.set_image_cache(tile_hash, (content))

    if timings:
        headers["X-Server-Timings"] = "; ".join(
            ["{} - {:0.2f}".format(name, time * 1000) for (name, time) in timings]
        )

    return TileResponse(content, media_type=mimetype["png"], headers=headers)
