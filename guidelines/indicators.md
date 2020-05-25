# Contributing Indicator Data
Timeseries indicator data is provided in CSV format. Each indicator requires:

- a metadata file describing the indicator
- time-series data for each spotlight area

For an overview of the current spotlight areas, see the [/sites API endpoint](https://8ib71h0627.execute-api.us-east-1.amazonaws.com/v1/sites).

## Data structure
Expected format:

- single CSV file per spotlight area
- each row contains values for a single timestep
- each row should have at least a column a date and a value
- numbers should be unquoted, and can’t contain thousand separators

### Example

``` csv
date,median,baseline_median,baseline_mean
12/27/2014,15.502651,20.564545686759864,221,610
12/28/2014,17.219058,10.755911295434752,244,607
```

## Metadata
In addition to the data itself, each indicator needs a metadata file with:

``` json
{ 
  "date": {
    "column": "date",
    "format": "y-MM-dd"
  },
  "indicator": {
    "column": "median"
  }
}
```

### Mandatory

- date
- indicator - main indicator

### Optional

- confidence intervals
- baseline
- baseline confidence intervals
- anomaly flag

## Delivery mechanism
Data can be provided to a S3 bucket:

- each indicator will have a separate folder on S3
- each file contains time-series data for a single spotlight area
- name of the file: [area ID].csv
- with each data update, the full file for the area needs to be replaced

### Example 
The contents of the bucket could look like:

```
s3://[bucket]/no2-15day/metadata.json
s3://[bucket]/no2-15day/be.csv
s3://[bucket]/no2-15day/la.csv
```
