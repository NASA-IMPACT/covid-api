# Using the API to explore and access datasets

The production API is currently accessible at this URL: https://8ib71h0627.execute-api.us-east-1.amazonaws.com/v1/

API documentation can be found under https://8ib71h0627.execute-api.us-east-1.amazonaws.com/docs 

Metadata and configuration information for all the datasets available in the dashboard can be found at the [`/datasets` endpoint](https://8ib71h0627.execute-api.us-east-1.amazonaws.com/v1/datasets). 

There are two categories of datasets: `global`, datasets that span the entire globe, and `spotlight`, datasets that only exist for certain spotlight cities/areas. The spotlight areas available and their metadata can be found at the [`/sites` endpoint](https://8ib71h0627.execute-api.us-east-1.amazonaws.com/v1/sites). 

Appending a site id from the `/sites` endpoint to the `/datasets` endpoint will return all the datasets that are available for that spotlight (ie: [`/datasets/be`](https://8ib71h0627.execute-api.us-east-1.amazonaws.com/v1/) will return all datasets available for the Beijing spotlight). The [`/datasets/global` endpoint](https://8ib71h0627.execute-api.us-east-1.amazonaws.com/v1/datasets/global) will return all of the global spotlights. Note that all global spotlights are also included in the datasets specific to a spotlight, since the data does exist for that spotlight. 

Here is the metadata for one of the datasets (Nightlights-VIIRS) availabe in the Beijing spotlight (dataset metadata for all Beijing datasets can be found at the `/datasets/be` enpoint)

```json

{
      "id": "nightlights-viirs",
      "name": "Nightlights VIIRS",
      "type": "raster-timeseries",
      "isPeriodic": true,
      "time_unit": "day",
      "domain": [
        "2020-01-01T00:00:00Z",
        "2020-12-01T00:00:00Z"
      ],
      "source": {
        "type": "raster",
        "tiles": [
          "https://8ib71h0627.execute-api.us-east-1.amazonaws.com/v1/{z}/{x}/{y}@1x?url=s3://covid-eo-data/bm_500m_daily/VNP46A2_V011_be_{date}_cog.tif&resampling_method=nearest&bidx=1&rescale=0%2C100&color_map=viridis"
        ]
      },
      "backgroundSource": null,
      "exclusiveWith": [
        "agriculture",
        "no2",
        "co2-diff",
        "co2",
        "gibs-population",
        "car-count",
        "nightlights-hd",
        "water-chlorophyll",
        "water-spm"
      ],
      "swatch": {
        "color": "#C0C0C0",
        "name": "Grey"
      },
      "compare": null,
      "legend": {
        "type": "gradient",
        "min": "less",
        "max": "more",
        "stops": [
          "#440357",
          "#3b508a",
          "#208f8c",
          "#5fc961",
          "#fde725"
        ]
      },
      "paint": null,
      "info": "Darker colors indicate fewer night lights and less activity. Lighter colors indicate more night lights and more activity. Check out the HD dataset to see a light-corrected version of this dataset."
    }
```
The dataset source tiles are under the key `source.tiles`. Items surrounded by curly braces `{` and `}` should be replaced with apropriate values. 

The `{x}` and `{y}` values, in combination with the zoom level, `{z}`, identify the [Slippy Map Tilename](https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames) of the tile to fetch. (eg: a tile containing Los Angeles has `/{z}/{x}/{y}` values: `9/87/204`).  

`{date}` should be of the format `YYYYMM`, if the value of `time_unit` is `month` , and `YYYY_MM_DD`, if the value of `time_unit` is `day`. 

Dates available for the dataset are given by the `domain` key. If the `isPeriodic` value is `True`, then `domain` will only contain 2 dates, the start and end date. Any date within that range will be valid (remember that dates can either be daily (`YYYY_MM_DD`) or monthly ( `YYYYMM`)). For example, a periodic, monthly dataset can be requested with `202001` as the `{date}` field, to get data for January 2020 and `202002` for February 2020). 

The URL for requesting data from the `nightlights-viirs` data for Beijing, for xyz coordinates `z=9, x=421, y=193` on January 1st, 2020 would look something like: 

[https://8ib71h0627.execute-api.us-east-1.amazonaws.com/v1/9/421/193@1x?url=s3://covid-eo-data/bm_500m_daily/VNP46A2_V011_be_2020_01_01_cog.tif&resampling_method=nearest&bidx=1&rescale=0%2C100&color_map=viridis](https://8ib71h0627.execute-api.us-east-1.amazonaws.com/v1/9/421/193@1x?url=s3://covid-eo-data/bm_500m_daily/VNP46A2_V011_be_2020_01_01_cog.tif&resampling_method=nearest&bidx=1&rescale=0%2C100&color_map=viridis)

Which will display in the browser.
