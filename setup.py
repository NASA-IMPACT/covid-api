"""Setup covid_api."""

from setuptools import find_packages, setup

with open("README.md") as f:
    long_description = f.read()

inst_reqs = [
    "fastapi==0.60.0",
    "jinja2",
    "python-binary-memcached",
    "rio-color",
    "rio-tiler==2.0a.11",
    "email-validator",
    "fiona",
    "shapely",
    "rasterstats",
    "geojson-pydantic",
    "boto3",
    "requests",
]
extra_reqs = {
    "dev": ["pytest", "pytest-cov", "pytest-asyncio", "pre-commit"],
    "server": ["uvicorn", "click==7.0"],
    "deploy": [
        "docker",
        "attrs~=19.3.0",
        "aws-cdk.core",
        "aws-cdk.aws_lambda",
        "aws-cdk.aws_apigatewayv2",
        "aws-cdk.aws_ecs",
        "aws-cdk.aws_ec2",
        "aws-cdk.aws_autoscaling",
        "aws-cdk.aws_ecs_patterns",
        "aws-cdk.aws_iam",
        "aws-cdk.aws_elasticache",
    ],
    "test": ["moto[iam]", "mock", "pytest", "pytest-cov", "pytest-asyncio", "requests"],
}


setup(
    name="covid_api",
    version="0.2.2",
    description=u"",
    long_description=long_description,
    long_description_content_type="text/markdown",
    python_requires=">=3",
    classifiers=[
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    keywords="",
    author=u"Development Seed",
    author_email="info@developmentseed.org",
    url="https://github.com/developmentseed/covid_api",
    license="MIT",
    packages=find_packages(exclude=["ez_setup", "examples", "tests"]),
    package_data={
        "covid_api": ["templates/*.html", "templates/*.xml", "db/static/**/*.json"]
    },
    include_package_data=True,
    zip_safe=False,
    install_requires=inst_reqs,
    extras_require=extra_reqs,
)
