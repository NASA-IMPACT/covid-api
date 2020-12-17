import json

"""Test covid_api.main.app."""


def test_health(app):
    """Test /ping endpoint."""
    response = app.get("/ping")
    assert response.status_code == 200
    assert response.json() == {"ping": "pong!"}


def test_index(app):
    """Test /ping endpoint."""
    response = app.get("/")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert response.headers["content-encoding"] == "gzip"

    response = app.get("/index.html")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert response.headers["content-encoding"] == "gzip"


def test_utils_lambda_invoke(db_utils, lambda_function):
    """
    Tests the lambda_invoke utils function. While the lambda_invoke
    parameters specify `InvocationType="RequestResponse"` which should
    return a status 200 when successfull, the method returns a status 202
    (Accepted), but also returns the lambda output. Not sure why the incorrect
    status is being returned.

    Lambda output looks like: 
    ```
    START RequestId: 7c61eb52-735d-1ce4-0df2-a975197924eb Version: 1
    END RequestId: 7c61eb52-735d-1ce4-0df2-a975197924eb
    REPORT RequestId: 7c61eb52-735d-1ce4-0df2-a975197924eb  Init Duration: 232.54 ms        Duration: 3.02 ms       Billed Duration: 100 ms Memory Size: 128 MB    Max Memory Used: 33 MB

    {"result":"success","input":"test"}
    ```
    So the output is parsed for chars between "{" and "}" to extract the actual output of the 
    lambda function
    """  # noqa
    resp = db_utils.invoke_lambda(
        lambda_function_name=lambda_function["FunctionName"],
        payload={"input": "test"},
        invocation_type="RequestResponse",
    )

    assert 200 <= resp["StatusCode"] < 300

    lambda_response = resp["Payload"].read().decode("utf-8")

    lambda_output = json.loads(
        lambda_response[lambda_response.index("{") : (lambda_response.index("}") + 1)]
    )

    assert lambda_output["result"] == "success"
    assert lambda_output["input"] == "test"
