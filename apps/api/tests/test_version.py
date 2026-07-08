from fastapi.testclient import TestClient

from main import app


def test_version_endpoint_returns_app_metadata():
    client = TestClient(app)

    response = client.get("/version")

    assert response.status_code == 200
    assert response.json() == {
        "app_name": "Library-Yui API",
        "version": "0.1.0",
        "milestone": "MVP 1 — Audio Downloads",
    }
