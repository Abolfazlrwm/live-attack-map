"""Generate demo attack events for local testing, screenshots, and Docker demos.

Usage:
    python tools/seed.py --count 50
"""

from __future__ import annotations

import argparse
import json
import random
from datetime import datetime, timezone
from pathlib import Path

CITIES = [
    {"country": "Russia", "country_code": "RU", "city": "Moscow", "lat": 55.7558, "lon": 37.6173},
    {"country": "China", "country_code": "CN", "city": "Shenzhen", "lat": 22.5431, "lon": 114.0579},
    {"country": "Brazil", "country_code": "BR", "city": "Sao Paulo", "lat": -23.5505, "lon": -46.6333},
    {"country": "Germany", "country_code": "DE", "city": "Berlin", "lat": 52.5200, "lon": 13.4050},
    {"country": "India", "country_code": "IN", "city": "New Delhi", "lat": 28.6139, "lon": 77.2090},
    {"country": "Indonesia", "country_code": "ID", "city": "Jakarta", "lat": -6.2088, "lon": 106.8456},
    {"country": "Nigeria", "country_code": "NG", "city": "Lagos", "lat": 6.5244, "lon": 3.3792},
    {"country": "South Korea", "country_code": "KR", "city": "Seoul", "lat": 37.5665, "lon": 126.9780},
    {"country": "Egypt", "country_code": "EG", "city": "Cairo", "lat": 30.0444, "lon": 31.2357},
    {"country": "Colombia", "country_code": "CO", "city": "Bogota", "lat": 4.7110, "lon": -74.0721},
    {"country": "Vietnam", "country_code": "VN", "city": "Hanoi", "lat": 21.0278, "lon": 105.8342},
    {"country": "Iran", "country_code": "IR", "city": "Isfahan", "lat": 32.6539, "lon": 51.6660},
]

USERNAMES = [
    "root", "admin", "ubuntu", "oracle", "postgres", "user", "test", "pi", "guest", "support",
]
PASSWORDS = [
    "123456", "password", "admin", "root", "toor", "1234", "qwerty", "letmein", "12345", "P@ssw0rd",
]
DEFAULT_LOG = Path("logs/attacks.jsonl")


def random_ip() -> str:
    return ".".join(str(random.randint(1, 223)) for _ in range(4))


def make_attack(rng: random.Random | None = None) -> dict:
    rng = rng or random
    city = rng.choice(CITIES)
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "src_ip": random_ip(),
        "src_port": rng.randint(1024, 65535),
        "username": rng.choice(USERNAMES),
        "password": rng.choice(PASSWORDS),
        "success": False,
        "country": city["country"],
        "country_code": city["country_code"],
        "city": city["city"],
        "lat": city["lat"],
        "lon": city["lon"],
        "demo": True,
    }


def seed_attacks(count: int = 60, log_path: Path = DEFAULT_LOG) -> int:
    """Append demo records and return the number written."""
    log_path = Path(log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        for _ in range(max(0, count)):
            handle.write(json.dumps(make_attack(), ensure_ascii=False) + "\n")
    return max(0, count)


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed demo attacks")
    parser.add_argument("--count", type=int, default=60)
    parser.add_argument("--log", type=Path, default=DEFAULT_LOG)
    args = parser.parse_args()
    written = seed_attacks(args.count, args.log)
    print(f"[*] Seeded {written} demo attacks -> {args.log}")


if __name__ == "__main__":
    main()
