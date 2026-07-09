from fastapi.testclient import TestClient

from main import app


def test_library_summary_returns_counts_for_all_storage_types():
    client = TestClient(app)

    response = client.get("/library/summary")

    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"audio", "video", "uploads", "thumbnails"}
    assert all(isinstance(value, int) and value >= 0 for value in body.values())
