"""IP geolocation with caching and graceful fallback."""

import threading

import requests

API_URL = "http://ip-api.com/json/{ip}?fields=status,country,countryCode,lat,lon,query"
UNKNOWN = {"country": "Unknown", "lat": None, "lon": None}

_cache: dict[str, dict] = {}
_lock = threading.Lock()


def geolocate(ip: str, timeout: float = 2.0) -> dict:
    with _lock:
        if ip in _cache:
            return _cache[ip]

    try:
        data = requests.get(API_URL.format(ip=ip), timeout=timeout).json()
    except (requests.RequestException, ValueError):
        data = {}

    if data.get("status") != "success":
        result = UNKNOWN
    else:
        result = {
            "country": data.get("country", "Unknown"),
            "lat": data.get("lat"),
            "lon": data.get("lon"),
        }

    with _lock:
        _cache[ip] = result
    return result