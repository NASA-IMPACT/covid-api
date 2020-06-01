# Data usage

Different types of data are used differently by COVID-DASHBOARD.  
This document outlines how the data can be presented to the user.

## COGs

*Coming soon*

## Charts

### Timeseries line chart

The timeseries line chart can be used to plot data over a given time period. It supports a main indicator value and its confidence zone (depicted in blue), a baseline value and its confidence zone, and highlight bands.
The chart is interactive, allowing the user to view the values on hover.

![Interactive chart gif](./images/chart-interactive.gif)

As listed in the [Contributing Indicators data](./indicators.md) document, only the `date` and `indicator` properties are required which will result in a simple chart

![Chart with indicator line](./images/chart-indicator.png)

If available in the dataset, the chart will show the confidence region for both the indicator and the baseline as a shaded version of the line color.

![Chart with indicator line and confidence](./images/chart-confidence.png)

The highlight bands are useful to call the user's attention to a specific time interval.  
They're defined by providing an interval with a start and end dates and an optional label.
Example:
```js
highlightBands: [
  {
    label: 'Emergency state',
    interval: ['2020-01-16', '2020-03-15']
  },
  {
    label: 'Lockdown',
    interval: ['2020-02-01', '2020-03-06']
  }
]
```

![Chart with indicator line and highlight bands](./images/chart-bands.png)