"""covid_api.api.utils."""

import csv
import hashlib
import json
import math
import random
import re
import time
from enum import Enum
from io import BytesIO
from typing import Any, Dict, Optional, Tuple

import numpy as np

# Temporary
import rasterio
import requests
from rasterio import features
from rasterio.io import MemoryFile
from rasterio.warp import transform_bounds
from rasterstats.io import bounds_window
from rio_color.operations import parse_operations
from rio_color.utils import scale_dtype, to_math_type
from rio_tiler import constants
from rio_tiler.mercator import get_zooms
from rio_tiler.utils import _chunks, has_alpha_band, has_mask_band, linear_rescale
from shapely.geometry import box, shape

from covid_api.core.config import INDICATOR_BUCKET, PLANET_API_KEY
from covid_api.db.memcache import CacheLayer
from covid_api.db.utils import s3_get
from covid_api.models.timelapse import Feature

from starlette.requests import Request


def get_cache(request: Request) -> CacheLayer:
    """Get Memcached Layer."""
    return request.state.cache


def get_hash(**kwargs: Any) -> str:
    """Create hash from kwargs."""
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
        indata, out_shape=shape, transform=affinetrans, fill=0, all_touched=all_touched
    )
    return rv_array


def rasterize_pctcover(geom, atrans, shape):
    """Rasterize features."""
    alltouched = _rasterize_geom(geom, shape, atrans, all_touched=True)
    exterior = _rasterize_geom(geom.exterior, shape, atrans, all_touched=True)

    # Create percent cover grid as the difference between them
    # at this point all cells are known 100% coverage,
    # we'll update this array for exterior points
    pctcover = alltouched - exterior

    # loop through indicies of all exterior cells
    for r, c in zip(*np.where(exterior == 1)):

        # Find cell bounds, from rasterio DatasetReader.window_bounds
        window = ((r, r + 1), (c, c + 1))
        ((row_min, row_max), (col_min, col_max)) = window
        x_min, y_min = (col_min, row_max) * atrans
        x_max, y_max = (col_max, row_min) * atrans
        bounds = (x_min, y_min, x_max, y_max)

        # Construct shapely geometry of cell
        cell = box(*bounds)

        # Intersect with original shape
        cell_overlap = cell.intersection(geom)

        # update pctcover with percentage based on area proportion
        pctcover[r, c] = cell_overlap.area / cell.area

    return pctcover


def get_zonal_stat(geojson: Feature, raster: str) -> Tuple[float, float]:
    """Return zonal statistics."""
    geom = shape(geojson.geometry.dict())
    with rasterio.open(raster) as src:
        # read the raster data matching the geometry bounds
        window = bounds_window(geom.bounds, src.transform)
        # store our window information & read
        window_affine = src.window_transform(window)
        data = src.read(window=window)

        # calculate the coverage of pixels for weighting
        pctcover = rasterize_pctcover(geom, atrans=window_affine, shape=data.shape[1:])

        return (
            np.average(data[0], weights=pctcover),
            np.nanmedian(data),
        )


# from https://gitlab.com/zfasnacht/global_mapping/-/blob/master/global_mapping.py#L231
no2_cmap = {
    0: [153, 197, 227, 255],
    1: [154, 197, 225, 255],
    2: [155, 198, 225, 255],
    3: [158, 198, 223, 255],
    4: [159, 199, 223, 255],
    5: [161, 200, 222, 255],
    6: [162, 200, 221, 255],
    7: [163, 201, 221, 255],
    8: [165, 201, 219, 255],
    9: [166, 202, 219, 255],
    10: [168, 203, 217, 255],
    11: [169, 203, 217, 255],
    12: [171, 203, 216, 255],
    13: [173, 204, 215, 255],
    14: [174, 205, 214, 255],
    15: [176, 206, 213, 255],
    16: [177, 206, 212, 255],
    17: [179, 207, 212, 255],
    18: [181, 207, 210, 255],
    19: [182, 208, 210, 255],
    20: [184, 209, 208, 255],
    21: [185, 209, 208, 255],
    22: [186, 209, 207, 255],
    23: [188, 210, 206, 255],
    24: [190, 211, 206, 255],
    25: [192, 211, 204, 255],
    26: [193, 212, 204, 255],
    27: [194, 212, 203, 255],
    28: [196, 213, 202, 255],
    29: [198, 214, 201, 255],
    30: [200, 214, 200, 255],
    31: [201, 215, 199, 255],
    32: [202, 215, 199, 255],
    33: [205, 216, 197, 255],
    34: [206, 217, 197, 255],
    35: [208, 217, 195, 255],
    36: [209, 218, 195, 255],
    37: [210, 218, 194, 255],
    38: [212, 219, 193, 255],
    39: [213, 219, 192, 255],
    40: [215, 220, 191, 255],
    41: [217, 221, 191, 255],
    42: [218, 221, 190, 255],
    43: [220, 222, 189, 255],
    44: [221, 222, 188, 255],
    45: [223, 223, 187, 255],
    46: [225, 224, 186, 255],
    47: [226, 224, 185, 255],
    48: [228, 225, 184, 255],
    49: [229, 225, 184, 255],
    50: [232, 226, 183, 255],
    51: [232, 226, 182, 255],
    52: [234, 227, 181, 255],
    53: [236, 228, 180, 255],
    54: [237, 228, 179, 255],
    55: [239, 229, 178, 255],
    56: [240, 229, 177, 255],
    57: [243, 230, 176, 255],
    58: [244, 231, 176, 255],
    59: [245, 231, 175, 255],
    60: [247, 232, 174, 255],
    61: [248, 232, 173, 255],
    62: [251, 233, 172, 255],
    63: [252, 234, 171, 255],
    64: [253, 232, 170, 255],
    65: [253, 230, 167, 255],
    66: [252, 226, 164, 255],
    67: [252, 222, 161, 255],
    68: [252, 220, 160, 255],
    69: [252, 216, 157, 255],
    70: [252, 213, 154, 255],
    71: [251, 209, 151, 255],
    72: [251, 206, 148, 255],
    73: [251, 203, 146, 255],
    74: [251, 200, 143, 255],
    75: [251, 197, 140, 255],
    76: [250, 193, 137, 255],
    77: [250, 189, 134, 255],
    78: [250, 186, 131, 255],
    79: [250, 183, 129, 255],
    80: [250, 181, 127, 255],
    81: [249, 177, 124, 255],
    82: [249, 174, 121, 255],
    83: [249, 170, 119, 255],
    84: [249, 168, 117, 255],
    85: [249, 165, 116, 255],
    86: [249, 162, 114, 255],
    87: [249, 158, 112, 255],
    88: [249, 155, 111, 255],
    89: [249, 153, 110, 255],
    90: [249, 150, 108, 255],
    91: [249, 147, 107, 255],
    92: [248, 144, 105, 255],
    93: [248, 141, 104, 255],
    94: [248, 139, 104, 255],
    95: [248, 136, 102, 255],
    96: [248, 133, 101, 255],
    97: [248, 130, 99, 255],
    98: [248, 126, 98, 255],
    99: [248, 124, 97, 255],
    100: [248, 121, 94, 255],
    101: [248, 118, 93, 255],
    102: [247, 115, 92, 255],
    103: [246, 112, 92, 255],
    104: [244, 110, 93, 255],
    105: [243, 108, 94, 255],
    106: [242, 106, 95, 255],
    107: [240, 103, 96, 255],
    108: [239, 101, 96, 255],
    109: [237, 99, 97, 255],
    110: [236, 97, 97, 255],
    111: [235, 95, 98, 255],
    112: [233, 92, 99, 255],
    113: [231, 90, 100, 255],
    114: [229, 87, 101, 255],
    115: [228, 85, 101, 255],
    116: [227, 83, 102, 255],
    117: [225, 80, 103, 255],
    118: [224, 78, 103, 255],
    119: [222, 76, 104, 255],
    120: [221, 74, 105, 255],
    121: [219, 71, 105, 255],
    122: [217, 70, 107, 255],
    123: [216, 69, 107, 255],
    124: [213, 68, 108, 255],
    125: [211, 67, 109, 255],
    126: [209, 67, 109, 255],
    127: [207, 65, 111, 255],
    128: [204, 65, 111, 255],
    129: [202, 63, 113, 255],
    130: [200, 63, 113, 255],
    131: [198, 62, 114, 255],
    132: [196, 61, 115, 255],
    133: [194, 60, 116, 255],
    134: [191, 58, 117, 255],
    135: [189, 58, 118, 255],
    136: [187, 57, 119, 255],
    137: [185, 56, 120, 255],
    138: [183, 55, 120, 255],
    139: [181, 54, 122, 255],
    140: [179, 53, 122, 255],
    141: [177, 53, 123, 255],
    142: [174, 51, 123, 255],
    143: [171, 51, 124, 255],
    144: [168, 49, 124, 255],
    145: [165, 49, 124, 255],
    146: [164, 48, 125, 255],
    147: [161, 47, 125, 255],
    148: [158, 46, 125, 255],
    149: [155, 45, 126, 255],
    150: [152, 44, 126, 255],
    151: [150, 44, 126, 255],
    152: [148, 43, 126, 255],
    153: [146, 42, 127, 255],
    154: [143, 41, 127, 255],
    155: [140, 40, 127, 255],
    156: [137, 39, 128, 255],
    157: [135, 38, 128, 255],
    158: [132, 38, 128, 255],
    159: [130, 36, 129, 255],
    160: [127, 36, 129, 255],
    161: [125, 34, 129, 255],
    162: [123, 34, 128, 255],
    163: [121, 33, 128, 255],
    164: [119, 32, 128, 255],
    165: [117, 32, 128, 255],
    166: [114, 31, 127, 255],
    167: [113, 30, 127, 255],
    168: [112, 30, 127, 255],
    169: [109, 28, 127, 255],
    170: [107, 28, 126, 255],
    171: [105, 27, 126, 255],
    172: [103, 26, 126, 255],
    173: [101, 25, 126, 255],
    174: [99, 24, 125, 255],
    175: [97, 24, 125, 255],
    176: [94, 23, 125, 255],
    177: [93, 22, 125, 255],
    178: [91, 21, 124, 255],
    179: [89, 20, 124, 255],
    180: [87, 20, 124, 255],
    181: [85, 19, 124, 255],
    182: [83, 18, 123, 255],
    183: [82, 18, 123, 255],
    184: [79, 17, 122, 255],
    185: [77, 17, 120, 255],
    186: [75, 17, 118, 255],
    187: [73, 17, 116, 255],
    188: [71, 17, 114, 255],
    189: [69, 17, 112, 255],
    190: [67, 17, 110, 255],
    191: [64, 17, 108, 255],
    192: [62, 17, 106, 255],
    193: [61, 17, 104, 255],
    194: [58, 17, 102, 255],
    195: [57, 17, 101, 255],
    196: [55, 16, 98, 255],
    197: [53, 16, 96, 255],
    198: [51, 16, 95, 255],
    199: [49, 16, 93, 255],
    200: [47, 16, 91, 255],
    201: [45, 16, 88, 255],
    202: [43, 16, 86, 255],
    203: [41, 16, 85, 255],
    204: [39, 16, 82, 255],
    205: [37, 16, 81, 255],
    206: [34, 16, 78, 255],
    207: [32, 16, 76, 255],
    208: [31, 16, 74, 255],
    209: [30, 16, 73, 255],
    210: [30, 15, 72, 255],
    211: [29, 15, 70, 255],
    212: [29, 15, 69, 255],
    213: [28, 14, 67, 255],
    214: [27, 14, 66, 255],
    215: [27, 14, 65, 255],
    216: [26, 14, 63, 255],
    217: [26, 14, 62, 255],
    218: [25, 13, 60, 255],
    219: [25, 13, 59, 255],
    220: [24, 13, 58, 255],
    221: [23, 12, 56, 255],
    222: [23, 12, 54, 255],
    223: [22, 12, 52, 255],
    224: [22, 12, 52, 255],
    225: [22, 11, 51, 255],
    226: [21, 11, 49, 255],
    227: [20, 11, 48, 255],
    228: [19, 10, 46, 255],
    229: [19, 10, 45, 255],
    230: [19, 10, 43, 255],
    231: [18, 10, 41, 255],
    232: [17, 9, 40, 255],
    233: [17, 9, 38, 255],
    234: [16, 9, 37, 255],
    235: [16, 9, 36, 255],
    236: [15, 8, 34, 255],
    237: [15, 8, 33, 255],
    238: [14, 8, 31, 255],
    239: [14, 8, 30, 255],
    240: [13, 7, 29, 255],
    241: [12, 7, 27, 255],
    242: [12, 7, 26, 255],
    243: [11, 6, 24, 255],
    244: [11, 6, 23, 255],
    245: [10, 6, 22, 255],
    246: [9, 6, 20, 255],
    247: [9, 5, 19, 255],
    248: [8, 5, 17, 255],
    249: [8, 5, 16, 255],
    250: [7, 5, 15, 255],
    251: [7, 4, 13, 255],
    252: [6, 4, 12, 255],
    253: [6, 4, 10, 255],
    254: [5, 4, 9, 255],
    255: [5, 3, 8, 255],
}

crop_monitor_cmap = {
    1: [120, 120, 120, 255],
    2: [130, 65, 0, 255],
    3: [66, 207, 56, 255],
    4: [245, 239, 0, 255],
    5: [241, 89, 32, 255],
    6: [168, 0, 0, 255],
    7: [0, 143, 201, 255],
}


COLOR_MAPS = {
    "no2": no2_cmap.copy(),
    "cropmonitor": crop_monitor_cmap.copy(),
}


def get_custom_cmap(cname) -> Dict:
    """Return custom colormap."""
    if not re.match(r"^custom_", cname):
        raise Exception("Invalid colormap name")
    _, name = cname.split("_")
    return COLOR_MAPS[name]


COLOR_MAP_NAMES = [
    "accent",
    "accent_r",
    "afmhot",
    "afmhot_r",
    "autumn",
    "autumn_r",
    "binary",
    "binary_r",
    "blues",
    "blues_r",
    "bone",
    "bone_r",
    "brbg",
    "brbg_r",
    "brg",
    "brg_r",
    "bugn",
    "bugn_r",
    "bupu",
    "bupu_r",
    "bwr",
    "bwr_r",
    "cfastie",
    "cividis",
    "cividis_r",
    "cmrmap",
    "cmrmap_r",
    "cool",
    "cool_r",
    "coolwarm",
    "coolwarm_r",
    "copper",
    "copper_r",
    "cubehelix",
    "cubehelix_r",
    "dark2",
    "dark2_r",
    "flag",
    "flag_r",
    "gist_earth",
    "gist_earth_r",
    "gist_gray",
    "gist_gray_r",
    "gist_heat",
    "gist_heat_r",
    "gist_ncar",
    "gist_ncar_r",
    "gist_rainbow",
    "gist_rainbow_r",
    "gist_stern",
    "gist_stern_r",
    "gist_yarg",
    "gist_yarg_r",
    "gnbu",
    "gnbu_r",
    "gnuplot",
    "gnuplot2",
    "gnuplot2_r",
    "gnuplot_r",
    "gray",
    "gray_r",
    "greens",
    "greens_r",
    "greys",
    "greys_r",
    "hot",
    "hot_r",
    "hsv",
    "hsv_r",
    "inferno",
    "inferno_r",
    "jet",
    "jet_r",
    "magma",
    "magma_r",
    "nipy_spectral",
    "nipy_spectral_r",
    "ocean",
    "ocean_r",
    "oranges",
    "oranges_r",
    "orrd",
    "orrd_r",
    "paired",
    "paired_r",
    "pastel1",
    "pastel1_r",
    "pastel2",
    "pastel2_r",
    "pink",
    "pink_r",
    "piyg",
    "piyg_r",
    "plasma",
    "plasma_r",
    "prgn",
    "prgn_r",
    "prism",
    "prism_r",
    "pubu",
    "pubu_r",
    "pubugn",
    "pubugn_r",
    "puor",
    "puor_r",
    "purd",
    "purd_r",
    "purples",
    "purples_r",
    "rainbow",
    "rainbow_r",
    "rdbu",
    "rdbu_r",
    "rdgy",
    "rdgy_r",
    "rdpu",
    "rdpu_r",
    "rdylbu",
    "rdylbu_r",
    "rdylgn",
    "rdylgn_r",
    "reds",
    "reds_r",
    "rplumbo",
    "schwarzwald",
    "seismic",
    "seismic_r",
    "set1",
    "set1_r",
    "set2",
    "set2_r",
    "set3",
    "set3_r",
    "spectral",
    "spectral_r",
    "spring",
    "spring_r",
    "summer",
    "summer_r",
    "tab10",
    "tab10_r",
    "tab20",
    "tab20_r",
    "tab20b",
    "tab20b_r",
    "tab20c",
    "tab20c_r",
    "terrain",
    "terrain_r",
    "twilight",
    "twilight_r",
    "twilight_shifted",
    "twilight_shifted_r",
    "viridis",
    "viridis_r",
    "winter",
    "winter_r",
    "wistia",
    "wistia_r",
    "ylgn",
    "ylgn_r",
    "ylgnbu",
    "ylgnbu_r",
    "ylorbr",
    "ylorbr_r",
    "ylorrd",
    "ylorrd_r",
] + [f"custom_{c}" for c in COLOR_MAPS.keys()]


ColorMapName = Enum("ColorMapNames", [(a, a) for a in COLOR_MAP_NAMES])  # type: ignore


def planet_mosaic_tile(scenes, x, y, z):
    """return a mosaicked tile for a set of planet scenes"""
    mosaic_tile = np.zeros((4, 256, 256), dtype=np.uint8)
    for scene in scenes:
        api_num = math.floor(random.random() * 3) + 1
        url = f"https://tiles{api_num}.planet.com/data/v1/PSScene3Band/{scene}/{z}/{x}/{y}.png?api_key={PLANET_API_KEY}"
        r = requests.get(url)
        with MemoryFile(BytesIO(r.content)) as memfile:
            with memfile.open() as src:
                data = src.read()
                # any place we don't have data yet, add some
                mosaic_tile = np.where(
                    mosaic_tile[3] == 0, mosaic_tile + data, mosaic_tile
                )

        # if the tile is full, stop
        if mosaic_tile[3].all():
            break

    # salt the resulting image
    salt = np.random.randint(0, 3, (256, 256), dtype=np.uint8)
    mosaic_tile[:3] = np.where(
        mosaic_tile[:3] < 254, mosaic_tile[:3] + salt, mosaic_tile[:3]
    )

    return mosaic_tile[:3], mosaic_tile[3]


def site_date_to_scenes(site: str, date: str):
    """get the scenes corresponding to detections for a given site and date"""
    # TODO: make this more generic
    # NOTE: detections folder has been broken up into `detections-plane` and `detections-ship`
    plane_site_date_to_scenes_csv = s3_get(
        INDICATOR_BUCKET, "detections-plane/detection_scenes.csv"
    )
    plane_site_date_lines = plane_site_date_to_scenes_csv.decode("utf-8").split("\n")

    ship_site_date_to_scenes_csv = s3_get(
        INDICATOR_BUCKET, "detections-ship/detection_scenes.csv"
    )
    ship_site_date_lines = ship_site_date_to_scenes_csv.decode("utf-8").split("\n")

    reader = list(csv.DictReader(plane_site_date_lines))
    reader.extend(list(csv.DictReader(ship_site_date_lines)))

    site_date_to_scenes_dict: dict = {}

    for row in reader:

        site_date_to_scenes_dict.setdefault(f'{row["aoi"]}-{row["date"]}', []).extend(
            json.loads(row["scene_id"].replace("'", '"'))
        )

    return site_date_to_scenes_dict[f"{site}-{date}"]
