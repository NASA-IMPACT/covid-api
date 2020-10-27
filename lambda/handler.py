"""AWS Lambda handler."""

from mangum import Mangum

from covid_api.main import app

handler = Mangum(app, enable_lifespan=False)
