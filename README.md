# covid-api

A lightweight tile server for COVID data, based on [titiler](https://github.com/developmentseed/titiler).

## Contributing data
More information for data contributors like expected input format and delivery mechanisms, can be found in the [data guidelines](guidelines/README.md).

## Local environment

First, add your AWS and Planet credentials to a new file called `.env`. You can see an example of this file at `.env.example`.

To run the API locally:

```
$ docker-compose up --build
```

The API should be running on `http://localhost:8000`.

## Contribution & Development

Issues and pull requests are more than welcome.

**dev install**

```bash
git clone https://github.com/NASA-IMPACT/covid-api.git
cd covid-api
pip install -e .
```

To run the app locally, generate a config file, generate static dataset json

```bash
# Copy and configure the app
cp stack/config.yml.example stack/config.yml
# Generate json metadata
export RUN_LOCAL=true
python -m lambda.dataset_metadata_generator.src.main
# Run the app
uvicorn covid_api.main:app --reload
```

This repo is set to use `pre-commit` to run *my-py*, *flake8*, *pydocstring* and *black* ("uncompromising Python code formatter") when commiting new code.

```bash
$ pre-commit install
```

```
$ git add .
$ git commit -m'fix a really important thing'
black....................................................................Passed
Flake8...................................................................Passed
Verifying PEP257 Compliance..............................................Passed
mypy.....................................................................Passed
[precommit cc12c5a] fix a really important thing
 ```

# Dataset Metadata

Metadata is used to list serve data via `/datasets`, `/tiles`, and `/timelapse` There are 2 possible sources of metadata for serving these resources.

1. Static JSON files, stored in `covid_api/db/static/datasets/`
2. STAC API, defined in `stack/config.yml`

## Generator Lambda

In `lambda/dataset_metadata_generator` is code for a lambda to asynchronously generate metadata json files.

This lambda generates metadata in 2 ways:
1. Reads through the s3 bucket to generate a file that contains the datasets for each given spotlight option (_all, global, tk, ny, sf, la, be, du, gh) and their respective domain for each spotlight.
2. Fetches collections from a STAC catalogue and generates a metadata object for each collection.
