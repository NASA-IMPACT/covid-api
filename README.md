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

### Installing the application

```bash
git clone https://github.com/NASA-IMPACT/covid-api.git
cd covid-api
pyenv install
pip install -e .
```
### Running tests

To run tests, this requires `tox` and python3.7:

You can manage python versions with [pyenv](https://github.com/pyenv/pyenv). `.python-version` specifies installation and local use of python3.7.

```bash
pip install tox
tox
```

### Running the app locally

To run the app locally, generate a config file and generate the static dataset json files.

NOTE: This requires read and write access to the s3 bucket in `stack/config.yml`.

```bash
# Copy and configure the app
cp stack/config.yml.example stack/config.yml
python -m lambda.dataset_metadata_generator.src.main
# Run the app
uvicorn covid_api.main:app --reload
```

### If developing on the appplication, use pre-commit

This repo is set to use `pre-commit` to run *my-py*, *flake8*, *pydocstring* and *black* ("uncompromising Python code formatter") when commiting new code.

```bash
$ pre-commit install
$ git add .
$ git commit -m'fix a really important thing'
black....................................................................Passed
Flake8...................................................................Passed
Verifying PEP257 Compliance..............................................Passed
mypy.....................................................................Passed
[precommit cc12c5a] fix a really important thing
 ```

### Modifying datasets

To modify the existing datasets, one can configure datasets to be listed by revising the list under `DATASETS: STATIC:`stack/config.yml` and / or listing datasets from an external STAC_API_URL.

Metadata is used to list serve data via `/datasets`, `/tiles`, and `/timelapse` There are 2 possible sources of metadata for serving these resources.

1. Static JSON files, stored in `covid_api/db/static/datasets/`
2. STAC API, defined in `stack/config.yml`

In `lambda/dataset_metadata_generator` is code for a lambda to asynchronously generate metadata json files.

This lambda generates metadata in 2 ways:

1. Reads through the s3 bucket to generate a file that contains the datasets for each given spotlight option (_all, global, tk, ny, sf, la, be, du, gh) and their respective domain for each spotlight.
2. If STAC_API_URL is configured in `stack/config.yml`, fetches collections from a STAC catalogue and generates a metadata object for each collection.

## Deployment

```bash
# Note: zsh users need to use
npm install -g aws-cdk
pip install -e ".[deploy]"

export AWS_PROFILE=CHANGEME
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity | jq .Account -r)
export AWS_REGION=$(aws configure get region)
cdk synth
cdk bootstrap aws://$AWS_ACCOUNT_ID/$AWS_REGION --all
```