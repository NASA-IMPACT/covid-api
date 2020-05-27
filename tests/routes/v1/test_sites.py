"""Test /v1/sites endpoints"""

def test_sites(app):
    """test /sites endpoint"""
    response = app.get("/v1/sites")
    assert response.status_code == 200

def test_site_id(app):
    """test /sites/{id} endpoint"""
    response = app.get("/v1/sites/be")
    assert response.status_code == 200
