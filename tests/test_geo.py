from __future__ import annotations

from dashboard import geo


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


def test_geolocate_success(monkeypatch):
    payload = {
        "status": "success",
        "country": "Russia",
        "countryCode": "RU",
        "city": "Moscow",
        "lat": 55.7558,
        "lon": 37.6173,
        "as": "AS12345 Example",
        "org": "Example ISP",
    }
    captured = {}

    def fake_get(url, **kwargs):
        captured["url"] = url
        captured["params"] = kwargs.get("params")
        return FakeResponse(payload)

    monkeypatch.setattr(geo.requests, "get", fake_get)
    result = geo.geolocate("8.8.8.8")
    assert result["country"] == "Russia"
    assert result["country_code"] == "RU"
    assert result["lat"] == 55.7558
    assert captured["params"]["fields"].startswith("status")


def test_geolocate_private_ip_never_calls_network(monkeypatch):
    def fail(*args, **kwargs):
        raise AssertionError("private addresses must not be sent to ip-api")

    monkeypatch.setattr(geo.requests, "get", fail)
    result = geo.geolocate("10.0.0.1")
    assert result["country"] == "Private / reserved"
    assert result["lat"] is None
    assert geo.geolocate("::1")["country"] == "Private / reserved"


def test_geolocate_fallback(monkeypatch):
    class Boom:
        def raise_for_status(self):
            raise geo.requests.RequestException("nope")

        def json(self):
            raise ValueError

    monkeypatch.setattr(geo.requests, "get", lambda *a, **k: Boom())
    assert geo.geolocate("8.8.4.4") == geo.UNKNOWN


def test_geolocation_cache(monkeypatch):
    calls = 0

    def fake_get(*args, **kwargs):
        nonlocal calls
        calls += 1
        return FakeResponse({"status": "success", "country": "Chile", "lat": -33.4, "lon": -70.6})

    monkeypatch.setattr(geo.requests, "get", fake_get)
    assert geo.geolocate("1.1.1.1")["country"] == "Chile"
    assert geo.geolocate("1.1.1.1")["country"] == "Chile"
    assert calls == 1


def test_is_public_ip():
    assert geo.is_public_ip("8.8.8.8")
    assert not geo.is_public_ip("192.168.1.10")
    assert not geo.is_public_ip("127.0.0.1")
    assert not geo.is_public_ip("not-an-ip")
