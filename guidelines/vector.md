# Contributing Vector Data

## Data structure
All vector data for the site is stored as [GeoJSON](https://geojson.org/). GeoJSON can be validated at [https://geojsonlint.com/](https://geojsonlint.com/) or with a variety of other software tools.

## Delivery mechanism

There are two mechanisms for making vector data available through this API:
- **send to API maintainers**: if you'd like to keep the source data stored privately, please contact olaf@developmentseed.org or drew@developmentseed.org, and we can discuss other hosting options for the data.
- **upload directly**: some science partners have direct S3 upload access. Those partners can upload to `s3://covid-eo-data/[dataset_folder]` where `[dataset_folder]` is an S3 folder containing the data. Each dataset should have a 1-1 relationship with a folder.
