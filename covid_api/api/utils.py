"""covid_api.api.utils."""

from typing import Any, Dict, Optional

import time
import json
import hashlib

import numpy as np
from affine import Affine
import fiona
from shapely.geometry import shape, box
from rasterstats.io import bounds_window

from starlette.requests import Request

# Temporary
import rasterio
from rasterio import features
from rasterio.warp import transform_bounds
from rio_tiler import constants
from rio_tiler.utils import has_alpha_band, has_mask_band
from rio_tiler.mercator import get_zooms

from rio_color.operations import parse_operations
from rio_color.utils import scale_dtype, to_math_type
from rio_tiler.utils import linear_rescale, _chunks

from covid_api.db.memcache import CacheLayer
from covid_api.models.timelapse import Feature


def get_cache(request: Request) -> CacheLayer:
    """Get Memcached Layer."""
    return request.state.cache


def get_hash(**kwargs: Any) -> str:
    """Create hash from a dict."""
    return hashlib.sha224(json.dumps(kwargs, sort_keys=True).encode()).hexdigest()


def postprocess(
    tile: np.ndarray,
    mask: np.ndarray,
    rescale: Optional[str] = None,
    color_formula: Optional[str] = None,
) -> np.ndarray:
    """Post-process tile data."""
    if rescale:
        rescale_arr = list(map(float, rescale.split(",")))
        rescale_arr = list(_chunks(rescale_arr, 2))
        if len(rescale_arr) != tile.shape[0]:
            rescale_arr = ((rescale_arr[0]),) * tile.shape[0]

        for bdx in range(tile.shape[0]):
            tile[bdx] = np.where(
                mask,
                linear_rescale(
                    tile[bdx], in_range=rescale_arr[bdx], out_range=[0, 255]
                ),
                0,
            )
        tile = tile.astype(np.uint8)

    if color_formula:
        # make sure one last time we don't have
        # negative value before applying color formula
        tile[tile < 0] = 0
        for ops in parse_operations(color_formula):
            tile = scale_dtype(ops(to_math_type(tile)), np.uint8)

    return tile


# from rio-tiler 2.0a5
def info(address: str) -> Dict:
    """
    Return simple metadata about the file.

    Attributes
    ----------
    address : str or PathLike object
        A dataset path or URL. Will be opened in "r" mode.

    Returns
    -------
    out : dict.

    """
    with rasterio.open(address) as src_dst:
        minzoom, maxzoom = get_zooms(src_dst)
        bounds = transform_bounds(
            src_dst.crs, constants.WGS84_CRS, *src_dst.bounds, densify_pts=21
        )
        center = [(bounds[0] + bounds[2]) / 2, (bounds[1] + bounds[3]) / 2, minzoom]

        def _get_descr(ix):
            """Return band description."""
            name = src_dst.descriptions[ix - 1]
            if not name:
                name = "band{}".format(ix)
            return name

        band_descriptions = [(ix, _get_descr(ix)) for ix in src_dst.indexes]
        tags = [(ix, src_dst.tags(ix)) for ix in src_dst.indexes]

        other_meta = dict()
        if src_dst.scales[0] and src_dst.offsets[0]:
            other_meta.update(dict(scale=src_dst.scales[0]))
            other_meta.update(dict(offset=src_dst.offsets[0]))

        if has_alpha_band(src_dst):
            nodata_type = "Alpha"
        elif has_mask_band(src_dst):
            nodata_type = "Mask"
        elif src_dst.nodata is not None:
            nodata_type = "Nodata"
        else:
            nodata_type = "None"

        try:
            cmap = src_dst.colormap(1)
            other_meta.update(dict(colormap=cmap))
        except ValueError:
            pass

        return dict(
            address=address,
            bounds=bounds,
            center=center,
            minzoom=minzoom,
            maxzoom=maxzoom,
            band_metadata=tags,
            band_descriptions=band_descriptions,
            dtype=src_dst.meta["dtype"],
            colorinterp=[src_dst.colorinterp[ix - 1].name for ix in src_dst.indexes],
            nodata_type=nodata_type,
            **other_meta,
        )


# This code is copied from marblecutter
#  https://github.com/mojodna/marblecutter/blob/master/marblecutter/stats.py
# License:
# Original work Copyright 2016 Stamen Design
# Modified work Copyright 2016-2017 Seth Fitzsimmons
# Modified work Copyright 2016 American Red Cross
# Modified work Copyright 2016-2017 Humanitarian OpenStreetMap Team
# Modified work Copyright 2017 Mapzen
class Timer(object):
    """Time a code block."""

    def __enter__(self):
        """Starts timer."""
        self.start = time.time()
        return self

    def __exit__(self, ty, val, tb):
        """Stops timer."""
        self.end = time.time()
        self.elapsed = self.end - self.start


# from https://gist.github.com/perrygeo/721040f8545272832a42#file-pctcover-png
# author: @perrygeo
def _rasterize_geom(geom, shape, affinetrans, all_touched):
    indata = [(geom, 1)]
    rv_array = features.rasterize(
        indata,
        out_shape=shape,
        transform=affinetrans,
        fill=0,
        all_touched=all_touched)
    return rv_array


def rasterize_pctcover(geom, atrans, shape):
    alltouched = _rasterize_geom(geom, shape, atrans, all_touched=True)
    exterior = _rasterize_geom(geom.exterior, shape, atrans, all_touched=True)

    # Create percent cover grid as the difference between them
    # at this point all cells are known 100% coverage,
    # we'll update this array for exterior points
    pctcover = (alltouched - exterior) * 100

    # loop through indicies of all exterior cells
    for r, c in zip(*np.where(exterior == 1)):

        # Find cell bounds, from rasterio DatasetReader.window_bounds
        window = ((r, r+1), (c, c+1))
        ((row_min, row_max), (col_min, col_max)) = window
        x_min, y_min = (col_min, row_max) * atrans
        x_max, y_max = (col_max, row_min) * atrans
        bounds = (x_min, y_min, x_max, y_max)

        # Construct shapely geometry of cell
        cell = box(*bounds)

        # Intersect with original shape
        cell_overlap = cell.intersection(geom)

        # update pctcover with percentage based on area proportion
        coverage = cell_overlap.area / cell.area
        pctcover[r, c] = int(coverage * 100)

    return pctcover

def get_zonal_stat(geojson: Feature, raster: str) -> float:
    geom = shape(geojson.geometry.dict())
    with rasterio.open(raster) as src:
        # read the raster data matching the geometry bounds
        window = bounds_window(geom.bounds, src.transform)
        # store our window information & read
        window_affine = src.window_transform(window)
        data = src.read(window=window)

        pctcover = rasterize_pctcover(
            geom,
            atrans=window_affine,
            shape=data.shape[1:]
        )

        return np.nanmean(data * pctcover)

