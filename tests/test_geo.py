from dashboard import geo


def test_geolocate_success(monkeypatch):
    class FakeResponse:
        def json(self):
            return {"status": "success", "country": "Russia", "lat": 55.7558, "lon": 37.6173}

    monkeypatch.setattr(geo.requests, "get", lambda *a, **k: FakeResponse())
    result = geo.geolocate("8.8.8.8")
    assert result["country"] == "Russia"
    assert result["lat"] == 55.7558


def test_geolocate_fallback(monkeypatch):
    class Boom:
        def json(self):
            raise ValueError

    monkeypatch.setattr(geo.requests, "get", lambda *a, **k: Boom())
    assert geo.geolocate("10.0.0.1") == geo.UNKNOWN