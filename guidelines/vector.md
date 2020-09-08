# Contributing Vector Data

## Data structure
All vector data for the site is stored as [GeoJSON](https://geojson.org/). GeoJSON can be validated at [https://geojsonlint.com/](https://geojsonlint.com/) or with a variety of other software tools.

## Naming convention

All vector files are currently used for representing machine learning predictions. They should be added to a folder named `detections-[type]` where type is the class name of the object being detected (e.g. ships, planes). After that, the GeoJSON files should be added to site specific folders, where sites can be found at https://8ib71h0627.execute-api.us-east-1.amazonaws.com/v1/sites. Then the file should be named with the date, formatted as:
- `YYYYMM` for monthly data
- `YYYY_MM_DD` for sub-monthly data (anything with daily or semi-periodic data)

So the final file path on AWS S3 will appear as:

```sh
s3://covid-eo-data/detections-[type]/[site]/[date].geojson
```

One example is:

```sh
s3://covid-eo-data/detections-ship/ny/2020_01_20.geojson
```

## Associated Raster Data

Please indicate if there is associated raster data which should be shown alongside the machine learning predictions. Current predictions are displayed along select imagery from [Planet](https://www.planet.com/)

## Delivery mechanism

There are two mechanisms for making vector data available through this API:
- **send to API maintainers**: if you'd like to keep the source data stored privately, please contact olaf@developmentseed.org or drew@developmentseed.org, and we can discuss other hosting options for the data.
- **upload directly**: some science partners have direct S3 upload access. Those partners can upload to `s3://covid-eo-data/[dataset_folder]` where `[dataset_folder]` is an S3 folder containing the data. Each dataset should have a 1-1 relationship with a folder.
