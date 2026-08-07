"""Generate demo attack events for local testing and screenshots.

Usage:
    python tools/seed.py --count 50
"""

import argparse
import json
import random
from datetime import datetime, timezone
from pathlib import Path

CITIES = [
    {"country": "Russia", "lat": 55.7558, "lon": 37.6173},
    {"country": "China", "lat": 22.5431, "lon": 114.0579},
    {"country": "Brazil", "lat": -23.5505, "lon": -46.6333},
    {"country": "Germany", "lat": 52.5200, "lon": 13.4050},
    {"country": "India", "lat": 28.6139, "lon": 77.2090},
    {"country": "Indonesia", "lat": -6.2088, "lon": 106.8456},
    {"country": "Nigeria", "lat": 6.5244, "lon": 3.3792},
    {"country": "South Korea", "lat": 37.5665, "lon": 126.9780},
    {"country": "Egypt", "lat": 30.0444, "lon": 31.2357},
    {"country": "Colombia", "lat": 4.7110, "lon": -74.0721},
    {"country": "Vietnam", "lat": 21.0278, "lon": 105.8342},
    {"country": "Iran", "lat": 32.6539, "lon": 51.6660},
]

USERNAMES = ["root", "admin", "ubuntu", "oracle", "postgres", "user", "test", "pi", "guest", "support"]
PASSWORDS = ["123456", "password", "admin", "root", "toor", "1234", "qwerty", "letmein", "12345", "P@ssw0rd"]


def random_ip() -> str:
    return ".".join(str(random.randint(1, 223)) for _ in range(4))


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed demo attacks")
    parser.add_argument("--count", type=int, default=60)
    parser.add_argument("--log", type=Path, default=Path("logs/attacks.jsonl"))
    args = parser.parse_args()

    args.log.parent.mkdir(parents=True, exist_ok=True)
    for _ in range(args.count):
        city = random.choice(CITIES)
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "src_ip": random_ip(),
            "src_port": random.randint(1024, 65535),
            "username": random.choice(USERNAMES),
            "password": random.choice(PASSWORDS),
            "success": False,
            "country": city["country"],
            "lat": city["lat"],
            "lon": city["lon"],
            "demo": True,
        }
        with args.log.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record) + "\n")
    print(f"[*] Seeded {args.count} demo attacks -> {args.log}")


if __name__ == "__main__":
    main()