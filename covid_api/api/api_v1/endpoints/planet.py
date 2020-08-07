"""API planet mosaic tiles."""
import csv
import json
from typing import Any, Dict

from functools import partial

from fastapi import APIRouter, Depends, Query, Path
from starlette.concurrency import run_in_threadpool

from rio_tiler.utils import render

from covid_api.api import utils
from covid_api.core.config import INDICATOR_BUCKET
from covid_api.db.memcache import CacheLayer
from covid_api.db.utils import s3_get
from covid_api.ressources.enums import ImageType
from covid_api.ressources.common import mimetype
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

# TODO: make this more generic
site_date_to_scenes_csv = s3_get(
    INDICATOR_BUCKET, "detections/plane/detection_scenes.csv"
)
site_date_lines = site_date_to_scenes_csv.decode("utf-8").split("\n")
reader = csv.DictReader(site_date_lines)
site_date_to_scenes = dict()
for row in reader:
    site_date_to_scenes[f'{row["aoi"]}-{row["date"]}'] = row["scene_id"].replace(
        "'", '"'
    )


@router.get(r"/planet/{z}/{x}/{y}", **tile_routes_params)
async def tile(
    z: int = Path(..., ge=0, le=30, description="Mercator tiles's zoom level"),
    x: int = Path(..., description="Mercator tiles's column"),
    y: int = Path(..., description="Mercator tiles's row"),
    date: str = Query(..., description="date of site for detections"),
    site: str = Query(..., description="id of site for detections"),
    cache_client: CacheLayer = Depends(utils.get_cache),
) -> TileResponse:
    """Handle /planet requests."""
    timings = []
    headers: Dict[str, str] = {}

    scenes = json.loads(site_date_to_scenes[f"{site}-{date}"])

    tile_hash = utils.get_hash(**dict(z=z, x=x, y=y, scenes=scenes, planet=True))

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
            cache_client.set_image_cache(tile_hash, (content, ImageType.png))

    if timings:
        headers["X-Server-Timings"] = "; ".join(
            ["{} - {:0.2f}".format(name, time * 1000) for (name, time) in timings]
        )

    return TileResponse(
        content, media_type=mimetype[ImageType.png.value], headers=headers
    )
