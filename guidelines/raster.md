# Contributing Raster Data

## Data structure
All raster data for the site is stored as [Cloud Optimized GeoTIFF](https://www.cogeo.org/) (COG). One way to validate that data is in the proper format is using [rio-cogeo](https://github.com/cogeotiff/rio-cogeo):

- First, check that it passes validation with `rio cogeo validate my_raster.tif`
- Then ensure that it has a `nodata` value set. You can see the nodata value like so:

```sh
rio insp my_raster.tif
>>> print(src.meta)
```

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

There are two mechanisms for making raster data available through this API:
- **publicly available**: any publicly available COG can be accessed through this API. Because the API is run on Amazon Web Services in the `us-east-1` region, data hosted on S3 in this region will have faster response times to the API.
- **send to API maintainers**: if you'd like to keep the source data stored privately, please contact olaf@developmentseed.org or drew@developmentseed.org, and we can discuss other hosting options for the data.
