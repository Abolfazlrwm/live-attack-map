"""Real-time attack dashboard: tails the honeypot log and streams events."""

import json
import os
import threading
import time
from pathlib import Path

from flask import Flask, jsonify, render_template
from flask_socketio import SocketIO

from .geo import geolocate

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "change-me")
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

LOG_PATH = Path(os.getenv("LOG_PATH", "logs/attacks.jsonl"))
TARGET = {
    "lat": float(os.getenv("TARGET_LAT", "35.6892")),
    "lon": float(os.getenv("TARGET_LON", "51.3890")),
    "label": os.getenv("TARGET_LABEL", "Honeypot"),
}

_recent: list[dict] = []
_recent_lock = threading.Lock()
_polling = False


def load_recent(limit: int = 50) -> list[dict]:
    if not LOG_PATH.exists():
        return []
    lines = LOG_PATH.read_text(encoding="utf-8", errors="ignore").strip().splitlines()
    records = []
    for line in lines[-limit:]:
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return records


def enrich(record: dict) -> dict:
    if record.get("lat") is None or record.get("lon") is None:
        geo = geolocate(record["src_ip"])
        record["lat"] = geo["lat"]
        record["lon"] = geo["lon"]
        record["country"] = geo["country"]
    record["target"] = TARGET
    return record


def tail_logs() -> None:
    """Watch the log file and broadcast new attacks to connected clients."""
    offset = LOG_PATH.stat().st_size if LOG_PATH.exists() else 0
    while True:
        time.sleep(1)
        if not LOG_PATH.exists():
            continue
        size = LOG_PATH.stat().st_size
        if size < offset:  # file rotated -> restart from beginning
            offset = 0
        if size == offset:
            continue
        with LOG_PATH.open("r", encoding="utf-8", errors="ignore") as fh:
            fh.seek(offset)
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                record = enrich(record)
                with _recent_lock:
                    _recent.append(record)
                    if len(_recent) > 200:
                        _recent.pop(0)
                socketio.emit("attack", record)
        offset = size


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/attacks")
def attacks():
    with _recent_lock:
        return jsonify(list(_recent))


@socketio.on("connect")
def on_connect():
    with _recent_lock:
        for record in _recent:
            socketio.emit("attack", record)


def main() -> None:
    global _polling
    if not _polling:
        _polling = True
        with _recent_lock:
            _recent.extend(enrich(r) for r in load_recent())
        socketio.start_background_task(tail_logs)
    
if __name__ == "__main__":
    main()
