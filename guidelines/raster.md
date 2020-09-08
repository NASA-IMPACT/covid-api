# Contributing Raster Data

## Data structure
All raster data for the site is stored as [Cloud Optimized GeoTIFF](https://www.cogeo.org/) (COG). One way to validate that data is in the proper format is using [rio-cogeo](https://github.com/cogeotiff/rio-cogeo):

- First, check that it passes validation with `rio cogeo validate my_raster.tif`
- Then ensure that it has a `nodata` value set and that it matches the value which represents non-valid pixels within your GeoTIFF. You can see the `nodata` value like so:

```sh
rio info my_raster.tif --nodata
```

*note: `nan` values in the data will not be treated as non-valid pixels unless the `nodata` tag is `nan`.*

This same library can also create a Cloud Optimized GeoTIFF with the following command:

```sh
rio cogeo create my_raster.tif my_cog_raster.tif
```

## Naming convention

New raster files are added to the dashboard manually so the naming convention is rather liberal. The only requirement is that for date-specific data, the file name must include the date, formatted as:
- `YYYYMM` for monthly data
- `YYYY_MM_DD` for sub-monthly data (anything with daily or semi-periodic data)

If the file doesn't have global coverage, please use a portion of the file name to indicate the spotlight area it covers. We provide data for the following [spotlight areas](https://8ib71h0627.execute-api.us-east-1.amazonaws.com/v1/sites). For example:

```sh
my_tif_tk_2020_02_19.tif # Data for Tokyo on February 19th, 2020.
```

## Metadata

When sending the data, please include the following information
- A short description (1-2 sentences) of the data to be included on the dashboard.
- The time and spatial domain covered by the dataset
- Best practices/standards of color maps for visualizing the data

## Delivery mechanism

There are three mechanisms for making raster data available through this API:
- **publicly available**: any publicly available COG can be accessed through this API. Because the API is run on Amazon Web Services in the `us-east-1` region, data hosted on S3 in this region will have faster response times to the API.
- **send to API maintainers**: if you'd like to keep the source data stored privately, please contact olaf@developmentseed.org or drew@developmentseed.org, and we can discuss other hosting options for the data.
- **upload directly**: some science partners have direct S3 upload access. Those partners can upload to `s3://covid-eo-data/[dataset_folder]` where `[dataset_folder]` is an S3 folder containing the data. Each dataset should have a 1-1 relationship with a folder.

## Visualization

Once ingested or otherwise made accessible, the data is available as map tiles as detailed in the [API documentation](https://8ib71h0627.execute-api.us-east-1.amazonaws.com/docs). There are a variety of parameters that can be used to customize the visualization, in particular, a [number of colormaps](https://github.com/cogeotiff/rio-tiler/blob/master/docs/colormap.md). The remaining parameter descriptions are shown [here](https://github.com/developmentseed/cogeo-tiler#tiles).
