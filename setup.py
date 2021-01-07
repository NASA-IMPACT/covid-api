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
        "attrs",
        "aws-cdk.core>=1.72.0",
        "aws-cdk.aws_lambda>=1.72.0",
        "aws-cdk.aws_apigatewayv2>=1.72.0",
        "aws-cdk.aws_apigatewayv2_integrations>=1.72.0",
        "aws-cdk.aws_ecs>=1.72.0",
        "aws-cdk.aws_ec2>=1.72.0",
        "aws-cdk.aws_autoscaling>=1.72.0",
        "aws-cdk.aws_ecs_patterns>=1.72.0",
        "aws-cdk.aws_iam>=1.72.0",
        "aws-cdk.aws_elasticache>=1.72.0",
    ],
    "test": ["moto[iam]", "mock", "pytest", "pytest-cov", "pytest-asyncio", "requests"],
}


setup(
    name="covid_api",
    version="0.3.5",
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
