from fastapi.testclient import TestClient

from app.routes.library import MAX_UPLOAD_BYTES
from app.storage import LIBRARY_DIR, STORAGE_DIRS
from main import app


def test_config_endpoint_returns_runtime_config(monkeypatch):
    monkeypatch.delenv("LIBRARY_YUI_DOWNLOADS_ENABLED", raising=False)
    client = TestClient(app)

    response = client.get("/config")

    assert response.status_code == 200
    body = response.json()
    assert body["downloads_enabled"] is False
    assert body["max_upload_bytes"] == MAX_UPLOAD_BYTES
    assert body["library_dirs"] == {
        "library": str(LIBRARY_DIR.resolve()),
        **{name: str(path.resolve()) for name, path in STORAGE_DIRS.items()},
    }


def test_config_endpoint_reports_download_flag_enabled(monkeypatch):
    monkeypatch.setenv("LIBRARY_YUI_DOWNLOADS_ENABLED", "1")
    client = TestClient(app)

    response = client.get("/config")

    assert response.status_code == 200
    assert response.json()["downloads_enabled"] is True


def test_config_endpoint_is_grouped_under_system_openapi_tag():
    client = TestClient(app)

    response = client.get("/openapi.json")

    assert response.status_code == 200
    config_operation = response.json()["paths"]["/config"]["get"]
    assert config_operation["tags"] == ["System"]
