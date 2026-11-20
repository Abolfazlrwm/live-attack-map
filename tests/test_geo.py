from __future__ import annotations

from dashboard import geo


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


def _ipwho_payload(**overrides):
    """A representative https://ipwho.is/<ip> response body."""
    payload = {
        "ip": "8.8.8.8",
        "success": True,
        "country": "Russia",
        "country_code": "RU",
        "city": "Moscow",
        "latitude": 55.7558,
        "longitude": 37.6173,
        "connection": {"asn": 12345, "org": "Example ISP", "isp": "Example ISP"},
    }
    payload.update(overrides)
    return payload


def test_geolocate_success(monkeypatch):
    payload = _ipwho_payload()
    captured = {}

    def fake_get(url, **kwargs):
        captured["url"] = url
        return FakeResponse(payload)

    monkeypatch.setattr(geo.requests, "get", fake_get)
    result = geo.geolocate("8.8.8.8")
    assert result["country"] == "Russia"
    assert result["country_code"] == "RU"
    assert result["city"] == "Moscow"
    assert result["lat"] == 55.7558
    assert result["lon"] == 37.6173
    assert result["asn"] == "AS12345"
    assert result["org"] == "Example ISP"
    # the provider must be contacted over HTTPS (no attacker-IP leakage)
    assert captured["url"].startswith("https://")


def test_geolocate_maps_missing_optional_fields(monkeypatch):
    def fake_get(url, **kwargs):
        return FakeResponse({"success": True, "country": "Nowhere"})

    monkeypatch.setattr(geo.requests, "get", fake_get)
    result = geo.geolocate("8.8.8.8")
    assert result["country"] == "Nowhere"
    assert result["country_code"] == ""
    assert result["asn"] == ""
    assert result["org"] == ""


def test_geolocate_private_ip_never_calls_network(monkeypatch):
    def fail(*args, **kwargs):
        raise AssertionError("private addresses must not be sent to the geo provider")

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


def test_geolocate_provider_failure_is_unknown(monkeypatch):
    # ipwho.is answers {"success": false, ...} instead of raising on bad input
    monkeypatch.setattr(
        geo.requests, "get", lambda *a, **k: FakeResponse({"success": False, "message": "Invalid IP"})
    )
    assert geo.geolocate("8.8.4.4") == geo.UNKNOWN


def test_geolocation_cache(monkeypatch):
    calls = 0

    def fake_get(*args, **kwargs):
        nonlocal calls
        calls += 1
        return FakeResponse(_ipwho_payload(country="Chile", latitude=-33.4, longitude=-70.6))

    monkeypatch.setattr(geo.requests, "get", fake_get)
    assert geo.geolocate("1.1.1.1")["country"] == "Chile"
    assert geo.geolocate("1.1.1.1")["country"] == "Chile"
    assert calls == 1


def test_is_public_ip():
    assert geo.is_public_ip("8.8.8.8")
    assert not geo.is_public_ip("192.168.1.10")
    assert not geo.is_public_ip("127.0.0.1")
    assert not geo.is_public_ip("not-an-ip")
