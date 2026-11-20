"""IP geolocation with caching, validation, and graceful fallback.

Only globally routable addresses are sent to the third-party service. Private,
loopback, link-local, multicast, and reserved addresses never leave the host.

The provider is ipwho.is over HTTPS: the honeypot feeds attacker IPs into this
module, so sending them to a third party over plain HTTP (ip-api.com's free
tier) would disclose which addresses are attacking the site to anyone who can
observe the traffic. ipwho.is offers the same lookup over HTTPS for free.
"""

from __future__ import annotations

import ipaddress
import threading
import time

import requests

API_URL = "https://ipwho.is/{ip}"
CACHE_TTL_SECONDS = 24 * 60 * 60
CACHE_MAX_ENTRIES = 10_000
UNKNOWN: dict[str, object] = {
    "country": "Unknown",
    "country_code": "",
    "city": "",
    "lat": None,
    "lon": None,
    "asn": "",
    "org": "",
}
RESERVED: dict[str, object] = {**UNKNOWN, "country": "Private / reserved"}

_cache: dict[str, tuple[float, dict[str, object]]] = {}
_lock = threading.Lock()


def is_public_ip(value: str) -> bool:
    """Return True only for a valid, globally routable unicast address."""
    try:
        address = ipaddress.ip_address(value.strip())
    except ValueError:
        return False
    return address.is_global


def _cached(ip: str) -> dict[str, object] | None:
    with _lock:
        entry = _cache.get(ip)
        if entry is None:
            return None
        expires_at, result = entry
        if expires_at <= time.monotonic():
            _cache.pop(ip, None)
            return None
        return dict(result)


def _store(ip: str, result: dict[str, object]) -> None:
    with _lock:
        if len(_cache) >= CACHE_MAX_ENTRIES:
            oldest = min(_cache, key=lambda key: _cache[key][0])
            _cache.pop(oldest, None)
        _cache[ip] = (time.monotonic() + CACHE_TTL_SECONDS, dict(result))


def clear_cache() -> None:
    """Clear the in-process cache. Primarily useful for tests."""
    with _lock:
        _cache.clear()


def geolocate(ip: str, timeout: float = 2.0) -> dict[str, object]:
    """Resolve an IP address, returning a stable dictionary shape.

    Network failures are cached briefly through the same path to avoid hammering
    the provider during an outage; callers always receive a usable record.
    """
    ip = ip.strip()
    if not is_public_ip(ip):
        return dict(RESERVED)

    cached = _cached(ip)
    if cached is not None:
        return cached

    try:
        response = requests.get(
            API_URL.format(ip=ip),
            timeout=timeout,
            headers={"User-Agent": "live-attack-map/1.x"},
        )
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError):
        data = {}

    if not isinstance(data, dict) or data.get("success") is not True:
        result = dict(UNKNOWN)
    else:
        connection = data.get("connection") or {}
        asn = connection.get("asn")
        result = {
            "country": data.get("country") or "Unknown",
            "country_code": data.get("country_code") or "",
            "city": data.get("city") or "",
            "lat": data.get("latitude"),
            "lon": data.get("longitude"),
            "asn": f"AS{asn}" if asn else "",
            "org": connection.get("org") or connection.get("isp") or "",
        }

    _store(ip, result)
    return dict(result)
