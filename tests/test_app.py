from dashboard.app import app


def test_index_serves_dashboard():
    client = app.test_client()
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"Live Attack Map" in resp.data


def test_api_returns_json():
    client = app.test_client()
    resp = client.get("/api/attacks")
    assert resp.status_code == 200
    assert isinstance(resp.get_json(), list)


def test_timeline_returns_buckets():
    client = app.test_client()
    resp = client.get("/api/timeline?minutes=5")
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data) == 5
    assert all("time" in d and "count" in d for d in data)