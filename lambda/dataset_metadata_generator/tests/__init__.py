"""
Dataset metadata generator lambda test class. This file contains dataset and site metadata
used by the unit tests. The data in this file should be updated to reflect and modification
in metadata content or format of the actual metadatda files (under `covid_api/db/static/`)
"""
DATASETS = [
    {
        "id": "co2",
        "name": "CO₂ (Avg)",
        "type": "raster-timeseries",
        "time_unit": "day",
        "s3_location": "xco2-mean",
        "is_periodic": True,
        "source": {
            "type": "raster",
            "tiles": [
                "{api_url}/{z}/{x}/{y}@1x?url=s3://covid-eo-data/xco2-mean/xco2_16day_mean.{date}.tif&resampling_method=bilinear&bidx=1&rescale=0.000408%2C0.000419&color_map=rdylbu_r&color_formula=gamma r {gamma}"
            ],
        },
        "exclusive_with": [
            "agriculture",
            "no2",
            "co2-diff",
            "gibs-population",
            "car-count",
            "nightlights-viirs",
            "nightlights-hd",
            "detection-multi",
            "water-chlorophyll",
            "water-spm",
            "detections-ship",
            "detections-plane",
            "detections-vehicles",
        ],
        "enabled": False,
        "compare": {
            "enabled": True,
            "help": "Compare with baseline",
            "year_diff": 0,
            "map_label": "{date}: Base vs Mean",
            "source": {
                "type": "raster",
                "tiles": [
                    "{api_url}/{z}/{x}/{y}@1x?url=s3://covid-eo-data/xco2-base/xco2_16day_base.{date}.tif&resampling_method=bilinear&bidx=1&rescale=0.000408%2C0.000419&color_map=rdylbu_r&color_formula=gamma r {gamma}"
                ],
            },
        },
        "swatch": {"color": "#189C54", "name": "Dark Green"},
        "legend": {
            "type": "gradient-adjustable",
            "min": "< 408 ppm",
            "max": "> 419 ppm",
            "stops": [
                "#313695",
                "#588cbf",
                "#a3d2e5",
                "#e8f6e8",
                "#fee89c",
                "#fba55c",
                "#e24932",
            ],
        },
        "info": "This layer shows the average background concentration of carbon dioxide (CO₂) in our atmosphere for 2020. Redder colors indicate more CO₂. Bluer colors indicate less CO₂.",
    },
    {
        "id": "detections-plane",
        "name": "Airplanes",
        "type": "inference-timeseries",
        "s3_location": "detections-plane",
        "is_periodic": False,
        "time_unit": "day",
        "source": {
            "type": "geojson",
            "tiles": ["{api_url}/detections-plane/{spotlightId}/{date}.geojson"],
        },
        "background_source": {
            "type": "raster",
            "tiles": ["{api_url}/planet/{z}/{x}/{y}?date={date}&site={spotlightId}"],
        },
        "exclusive_with": [
            "agriculture",
            "no2",
            "co2-diff",
            "co2",
            "gibs-population",
            "car-count",
            "nightlights-viirs",
            "nightlights-hd",
            "detection-multi",
            "water-chlorophyll",
            "water-spm",
            "detections-ship",
            "detections-vehicles",
        ],
        "enabled": False,
        "swatch": {"color": "#C0C0C0", "name": "Grey"},
        "info": "Grounded airplanes detected each day in PlanetScope imagery are shown in orange.",
    },
    {
        "id": "nightlights-hd",
        "name": "Nightlights HD",
        "type": "raster-timeseries",
        "s3_location": "bmhd_30m_monthly",
        "is_periodic": True,
        "time_unit": "month",
        "source": {
            "type": "raster",
            "tiles": [
                "{api_url}/{z}/{x}/{y}@1x?url=s3://covid-eo-data/bmhd_30m_monthly/BMHD_VNP46A2_{spotlightId}_{date}_cog.tif&resampling_method=bilinear&bidx=1%2C2%2C3"
            ],
        },
        "exclusive_with": [
            "agriculture",
            "no2",
            "co2-diff",
            "co2",
            "gibs-population",
            "car-count",
            "nightlights-viirs",
            "detection-multi",
            "water-chlorophyll",
            "water-spm",
            "detections-ship",
            "detections-plane",
            "detections-vehicles",
        ],
        "swatch": {"color": "#C0C0C0", "name": "Grey"},
        "legend": {
            "type": "gradient",
            "min": "less",
            "max": "more",
            "stops": ["#08041d", "#1f0a46", "#52076c", "#f57c16", "#f7cf39"],
        },
        "info": "The High Definition Nightlights dataset is processed to eliminate light sources, including moonlight reflectance and other interferences. Darker colors indicate fewer night lights and less activity. Lighter colors indicate more night lights and more activity.",
    },
    {
        "id": "nightlights-viirs",
        "name": "Nightlights VIIRS",
        "type": "raster-timeseries",
        "time_unit": "day",
        "s3_location": "bm_500m_daily",
        "is_periodic": True,
        "source": {
            "type": "raster",
            "tiles": [
                "{api_url}/{z}/{x}/{y}@1x?url=s3://covid-eo-data/bm_500m_daily/VNP46A2_V011_{spotlightId}_{date}_cog.tif&resampling_method=nearest&bidx=1&rescale=0%2C100&color_map=viridis"
            ],
        },
        "exclusive_with": [
            "agriculture",
            "no2",
            "co2-diff",
            "co2",
            "gibs-population",
            "car-count",
            "nightlights-hd",
            "detection-multi",
            "water-chlorophyll",
            "water-spm",
            "detections-ship",
            "detections-plane",
            "detections-vehicles",
        ],
        "swatch": {"color": "#C0C0C0", "name": "Grey"},
        "legend": {
            "type": "gradient",
            "min": "less",
            "max": "more",
            "stops": ["#440357", "#3b508a", "#208f8c", "#5fc961", "#fde725"],
        },
        "info": "Darker colors indicate fewer night lights and less activity. Lighter colors indicate more night lights and more activity. Check out the HD dataset to see a light-corrected version of this dataset.",
    },
    {
        "id": "water-chlorophyll",
        "name": "Chlorophyll",
        "type": "raster-timeseries",
        "time_unit": "day",
        "is_periodic": False,
        "s3_location": "oc3_chla_anomaly",
        "source": {
            "type": "raster",
            "tiles": [
                "{api_url}/{z}/{x}/{y}@1x?url=s3://covid-eo-data/oc3_chla_anomaly/anomaly-chl-{spotlightId}-{date}.tif&resampling_method=bilinear&bidx=1&rescale=-100%2C100&color_map=rdbu_r"
            ],
        },
        "exclusive_with": [
            "agriculture",
            "no2",
            "co2-diff",
            "co2",
            "gibs-population",
            "car-count",
            "nightlights-viirs",
            "nightlights-hd",
            "detection-multi",
            "water-spm",
            "detections-ship",
            "detections-plane",
            "detections-vehicles",
        ],
        "swatch": {"color": "#154F8D", "name": "Deep blue"},
        "legend": {
            "type": "gradient",
            "min": "less",
            "max": "more",
            "stops": ["#3A88BD", "#C9E0ED", "#E4EEF3", "#FDDCC9", "#DE725B", "#67001F"],
        },
        "info": "Chlorophyll is an indicator of algae growth. Redder colors indicate increases in chlorophyll-a and worse water quality. Bluer colors indicate decreases in chlorophyll-a and improved water quality. White areas indicate no change.",
    },
]
SITES = [
    {
        "id": "du",
        "label": "Port of Dunkirk",
        "center": [2.250141, 51.02986],
        "polygon": {
            "type": "Polygon",
            "coordinates": [
                [
                    [2.08355962, 51.03423481],
                    [2.14826632, 50.96553938],
                    [2.41646888, 51.02097784],
                    [2.38289168, 51.07488218],
                    [2.32298564, 51.08773119],
                    [2.15844656, 51.05891125],
                    [2.08355962, 51.03423481],
                ]
            ],
        },
        "bounding_box": [2.008355962, 50.96553938, 2.41646888, 51.08773119],
    },
    {
        "id": "ny",
        "label": "New York",
        "center": [-73.09, 41.0114],
        "polygon": {
            "type": "Polygon",
            "coordinates": [
                [
                    [-71.74516, 41.54467],
                    [-74.43395, 41.54943],
                    [-74.43219, 40.47812],
                    [-71.74516, 40.48343],
                    [-71.74516, 41.54467],
                ]
            ],
        },
        "bounding_box": [-74.43395, 40.47812, -71.74516, 41.54467],
    },
    {
        "id": "tk",
        "label": "Tokyo",
        "center": [139.78, 35.61],
        "polygon": {
            "type": "Polygon",
            "coordinates": [
                [
                    [139.37, 35.33],
                    [140.19, 35.33],
                    [140.19, 35.85],
                    [139.37, 35.85],
                    [139.37, 35.33],
                ]
            ],
        },
        "bounding_box": [139.37, 35.33, 140.19, 35.85],
    },
]
