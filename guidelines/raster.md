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

## Delivery mechanism

There are three mechanisms for making raster data available through this API:
- **publicly available**: any publicly available COG can be accessed through this COG. Because the API is run on Amazon Web Services in the `us-east-1` region, data hosted on S3 in this region will have faster response times to the API.
- **grant access**: if data is hosted on a private Amazon Web Services S3 bucket, you can contact the API maintainers, olaf@developmentseed.org or drew@developmentseed.org, to provide necessary roles to access the data.
- **send to API maintainers**: if neither of these options work, please contact us, and we can discuss other hosting options for the data.
