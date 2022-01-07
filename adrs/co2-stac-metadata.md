# STAC metadata design for CO2 dataset

## Status

Proposed

## Context

The decision to use a STAC API as the backend for the climate dashboard arose the need to design STAC metadata for the model data and thematic data. This ADR deals with the design for one of the thematic data - CO2.

## Decision

Each of the thematic dataset (in this case, CO2) will be a STAC item.

Depending on the usability, it might make sense to make some custom STAC extensions for some of the metadata like legend, swatch, etc.

The proposed CO2 stac metadata is linked [here](co2.json).

## Consequences

Relative to the current implementation of frontend, there will be a few changes to how we access each of the dataset metadata since the keys/values have been rearranged to better align with the STAC spec.

However, this alignment with the STAC API will improve interoperatibility and extensibiliy.
