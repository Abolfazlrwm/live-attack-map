from __future__ import annotations

from datetime import datetime, timezone

from dashboard import app as app_module
from dashboard.app import app, socketio
from dashboard.geo import UNKNOWN


def _record(**overrides):
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "src_ip": "8.8.8.8",
        "src_port": 12345,
        "username": "root",
        "password": "toor",
        "success": False,
        "country": "United States",
        "lat": 37.751,
        "lon": -97.822,
    }
    record.update(overrides)
    return record


def test_index_serves_dashboard():
    client = app.test_client()
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"Live Attack Map" in resp.data


def test_healthz():
    resp = app.test_client().get("/healthz")
    assert resp.status_code == 200
    payload = resp.get_json()
    assert payload["status"] == "ok"
    assert payload["version"] == "1.0.1"


def test_config_serves_target():
    payload = app.test_client().get("/api/config").get_json()
    assert set(payload["target"]) == {"lat", "lon", "label"}
    assert payload["target"]["label"] == "Honeypot"
    assert payload["max_recent"] >= 50


def test_api_attacks_and_limits():
    with app_module._recent_lock:
        app_module._recent.append(_record())
    client = app.test_client()
    assert len(client.get("/api/attacks").get_json()) == 1
    assert client.get("/api/attacks?limit=0").get_json()[0]["username"] == "root"
    assert client.get("/api/attacks?limit=nope").status_code == 400


def test_timeline_returns_buckets():
    with app_module._recent_lock:
        app_module._recent.append(_record())
    resp = app.test_client().get("/api/timeline?minutes=5")
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data) == 5
    assert sum(item["count"] for item in data) == 1
    assert all("time" in item and "count" in item for item in data)


def test_timeline_rejects_invalid_minutes():
    client = app.test_client()
    assert client.get("/api/timeline?minutes=zero").status_code == 400
    assert client.get("/api/timeline?minutes=0").status_code == 400
    assert client.get("/api/timeline?minutes=9999").status_code == 400


def test_history_is_emitted_only_to_new_client():
    with app_module._recent_lock:
        app_module._recent.append(_record())

    first = socketio.test_client(app)
    first_events = [item for item in first.get_received() if item["name"] == "attack"]
    assert len(first_events) == 1

    second = socketio.test_client(app)
    second_events = [item for item in second.get_received() if item["name"] == "attack"]
    assert len(second_events) == 1

    # Connecting the second browser must not re-broadcast history to the first.
    assert [item for item in first.get_received() if item["name"] == "attack"] == []
    first.disconnect()
    second.disconnect()


def test_frontend_has_no_untrusted_innerhtml_sink():
    source = (app_module.Path(app_module.__file__).parent / "templates" / "index.html").read_text()
    assert "innerHTML" not in source
    assert "insertAdjacentHTML" not in source
    assert "textContent" in source


def test_queue_record_skips_network_for_seeded_coordinates(monkeypatch):
    def fail(*args, **kwargs):
        raise AssertionError("seeded records must not hit the geolocation API")

    monkeypatch.setattr(app_module, "geolocate", fail)
    app_module.queue_record(_record())
    with app_module._recent_lock:
        assert len(app_module._recent) == 1
    assert app_module._geo_queue.empty()


def test_queue_record_marks_reserved_ip(monkeypatch):
    def fail(*args, **kwargs):
        raise AssertionError("reserved IPs must not hit the geolocation API")

    monkeypatch.setattr(app_module, "geolocate", fail)
    app_module.queue_record(_record(src_ip="10.0.0.7", country=None, lat=None, lon=None))
    with app_module._recent_lock:
        saved = app_module._recent[-1]
    assert saved["country"] == "Private / reserved"
    assert app_module._geo_queue.empty()


def test_queue_record_defers_public_lookup(monkeypatch):
    monkeypatch.setattr(app_module, "geolocate", lambda _ip: dict(UNKNOWN))
    app_module.queue_record(_record(lat=None, lon=None, country=None))
    assert app_module._geo_queue.qsize() == 1
    with app_module._recent_lock:
        assert len(app_module._recent) == 0
