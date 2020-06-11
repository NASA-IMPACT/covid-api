# Contributing Indicator Data
Timeseries indicator data is provided in CSV format. It's mostly used in the dashboard in charts that show [evolution over time](./data-usage.md)).

Each indicator requires:

- a metadata file describing the indicator
- time-series data for each spotlight area

For an overview of the current spotlight areas, see the [/sites API endpoint](https://8ib71h0627.execute-api.us-east-1.amazonaws.com/v1/sites).

## Data structure
Expected format:

- single CSV file per spotlight area
- each row contains values for a single timestep
- each row should have at least a column with a date and an indicator value
- numbers should be unquoted, can’t contain thousand separators, and must be parsable as `float` by python
- all columns indicated as relevant by the metadata should be numbers except for `date` and optionally `anomaly`
- exactly one header row showing column names in the first row

### Error / Fill values
Don't include rows with error or fill values like `-999`.

```
27/01/2020,-999,7.21537286398442,-999,8.03568780281027,-999,-999
```

Omit these rows, the frontend is built to deal with missing data.

### Example

``` csv
date_obs,median,baseline_median,baseline_mean
02/07/2014,15.502651,20.564545686759864,221,610
02/08/2014,17.219058,10.755911295434752,244,607
```

## Metadata
In addition to the data itself, each indicator needs a metadata file with:

``` json
{
  "date": {
    "column": "date_obs",
    "format": "%d/%m/%Y"
  },
  "indicator": {
    "column": "median"
  },
  "baseline": {
    "column": "baseline_median"
  },
  "highlight_bands": [
    {
      "label": "Lockdown",
      "interval": ["2020-02-01", "2020-03-06"]
    }
  ]
}
```

The date format should use options found in the [python `strptime` documentation](https://docs.python.org/3.7/library/datetime.html#strftime-and-strptime-behavior)

### Mandatory fields

- `date`: the column where each observation date is shown and the format used to correctly parse it
- `indicator` - the primary indicator column

### Optional fields

- `indicator_conf_low` and `indicator_conf_high`: columns used for confidence intervals
- `baseline`: columns used for a baseline value to compare with the primary indicator
- `baseline_conf_low` and `baseline_conf_high`: columns used for confidence intervals for the baseline values
- `anomaly`: column used to indicate if the value is anomalous, accepts any string

### Additional Metadata

For any commentary which is both indicator and site specific, additional `.json` files can be added alongside the csv files. So for example, `be.csv` can have a `be.json` file which adds contextual information for what is happening with a given indicator in Beijing. This JSON object can have two properties:
- `notes`: text field to be added below the chart
- `highlight_bands`: used to highlight a time interval on the chart (eg. lockdown)

An example metadata file looks like this:

```json
{
    "notes": "description",
    "highlight_bands": [
        {
          "label": "Detection",
          "interval": ["2020-02-01", "2020-03-30"]
        },
        {
          "label": "Emergency state",
          "interval": ["2020-03-15", "2020-05-15"]
        }
      ]
}
```

## Delivery mechanism
Data can be provided to a S3 bucket:

- each indicator will have a separate folder on S3
- each file contains time-series data for a single spotlight area
- name of the file: [area ID].csv
- with each data update, the full file for the area needs to be replaced

## Examples

### NO2 15 day average

[`/no2-omi/metadata.json`](https://covid-eo-example.s3.amazonaws.com/no2-omi/metadata.json)
[`/no2-omi/be.csv`](https://covid-eo-example.s3.amazonaws.com/no2-omi/be.csv)
[`/no2-omi/du.csv`](https://covid-eo-example.s3.amazonaws.com/no2-omi/du.csv)
[`/no2-omi/ls.csv`](https://covid-eo-example.s3.amazonaws.com/no2-omi/ls.csv)
