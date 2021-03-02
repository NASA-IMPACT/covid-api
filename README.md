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
$ git clone https://github.com/NASA-IMPACT/covid-api.git
$ cd covid-api
$ pip install -e .[dev]
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

 ## Development

 ```bash
 pip install -e . --no-cache-dir
 uvicorn covid_api.main:app --reload
 ```