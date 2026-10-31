"""Real-time attack dashboard: follows the honeypot log and streams events."""

from __future__ import annotations

import json
import logging
import os
import queue
import secrets
import threading
import time
from collections import deque
from datetime import datetime, timedelta, timezone
from pathlib import Path

from flask import Flask, jsonify, render_template, request
from flask_socketio import SocketIO, emit

from . import __version__
from .geo import geolocate, is_public_ip
from .tailer import LogTailer

logger = logging.getLogger(__name__)

app = Flask(__name__)
_secret_key = os.getenv("SECRET_KEY", "").strip()
if not _secret_key:
    _secret_key = secrets.token_hex(32)
    logger.warning("SECRET_KEY is unset; using an ephemeral key (sessions will not persist)")
app.config["SECRET_KEY"] = _secret_key
app.config["MAX_CONTENT_LENGTH"] = 64 * 1024

_origins = [item.strip() for item in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",") if item.strip()]
socketio = SocketIO(
    app,
    cors_allowed_origins=_origins or None,
    async_mode="threading",
)

LOG_PATH = Path(os.getenv("LOG_PATH", "logs/attacks.jsonl"))
MAX_RECENT = max(50, min(int(os.getenv("MAX_RECENT", "500")), 5000))
TARGET = {
    "lat": float(os.getenv("TARGET_LAT", "35.6892")),
    "lon": float(os.getenv("TARGET_LON", "51.3890")),
    "label": os.getenv("TARGET_LABEL", "Honeypot"),
}

_recent: deque[dict] = deque(maxlen=MAX_RECENT)
_recent_lock = threading.Lock()
_geo_queue: queue.Queue[dict] = queue.Queue(maxsize=MAX_RECENT)
_services_lock = threading.Lock()
_services_started = False
_tailer = LogTailer(LOG_PATH)
_started_at = time.time()


def parse_timestamp(value: object) -> datetime | None:
    """Parse an ISO-8601 timestamp, accepting a trailing ``Z`` on Python 3.10."""
    if not isinstance(value, str):
        return None
    text = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def load_recent(limit: int = 50) -> list[dict]:
    """Load the last complete JSON records without holding the whole log in RAM."""
    if not LOG_PATH.exists():
        return []
    lines: deque[str] = deque(maxlen=max(1, limit))
    with LOG_PATH.open("r", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            if line.strip():
                lines.append(line)
    records: list[dict] = []
    for line in lines:
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            records.append(value)
    return records


def enrich(record: dict) -> dict:
    """Attach presentation-only fields; never mutate the source record in place."""
    enriched = dict(record)
    enriched["target"] = dict(TARGET)
    return enriched


def _publish(record: dict) -> None:
    enriched = enrich(record)
    with _recent_lock:
        _recent.append(enriched)
    socketio.emit("attack", enriched)


def queue_record(record: dict) -> None:
    """Publish immediately when possible, otherwise resolve geodata off-thread."""
    has_coordinates = record.get("lat") is not None and record.get("lon") is not None
    ip = str(record.get("src_ip", ""))
    if has_coordinates or not is_public_ip(ip):
        if not has_coordinates and not record.get("country"):
            record = {**record, "country": "Private / reserved"}
        _publish(record)
        return
    try:
        _geo_queue.put_nowait(record)
    except queue.Full:
        _publish({**record, "country": "Unknown"})


def _geo_worker() -> None:
    while True:
        record = _geo_queue.get()
        try:
            result = geolocate(str(record.get("src_ip", "")))
            _publish({**record, **result})
        except Exception:  # a resolver failure must never kill the stream
            logger.exception("Geolocation worker failed")
            _publish({**record, "country": "Unknown"})
        finally:
            _geo_queue.task_done()


def _tail_worker() -> None:
    while True:
        try:
            lines = _tailer.read_new_lines()
            for line in lines:
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(record, dict):
                    queue_record(record)
        except OSError:
            logger.exception("Unable to read the attack log")
        socketio.sleep(1)


def start_background_services() -> None:
    """Start the log follower and geolocation worker exactly once per process."""
    global _services_started
    if app.config.get("TESTING"):
        return
    with _services_lock:
        if _services_started:
            return
        _services_started = True
        for record in reversed(load_recent(MAX_RECENT)):
            queue_record(record)
        socketio.start_background_task(_geo_worker)
        socketio.start_background_task(_tail_worker)
        logger.info("Dashboard background services started (log=%s)", LOG_PATH)


@app.before_request
def _ensure_services() -> None:
    start_background_services()


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/healthz")
def healthz():
    return jsonify(
        status="ok",
        version=__version__,
        uptime_seconds=round(time.time() - _started_at, 1),
        recent_events=len(_recent),
    )


@app.get("/api/config")
def config():
    return jsonify(
        target=dict(TARGET),
        max_recent=MAX_RECENT,
        version=__version__,
    )


@app.get("/api/attacks")
def attacks():
    try:
        limit = int(request.args.get("limit", str(MAX_RECENT)))
    except ValueError:
        return jsonify(error="limit must be an integer"), 400
    limit = max(1, min(limit, MAX_RECENT))
    with _recent_lock:
        values = list(_recent)[-limit:]
    return jsonify(values)


@app.get("/api/timeline")
def timeline():
    """Attack counts bucketed per minute, for the last ``minutes`` (default 30)."""
    try:
        minutes = int(request.args.get("minutes", "30"))
    except ValueError:
        return jsonify(error="minutes must be an integer"), 400
    if not 1 <= minutes <= 1440:
        return jsonify(error="minutes must be between 1 and 1440"), 400

    now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    buckets = {now - timedelta(minutes=i): 0 for i in range(minutes - 1, -1, -1)}
    with _recent_lock:
        records = list(_recent)
    for record in records:
        timestamp = parse_timestamp(record.get("timestamp"))
        if timestamp is None:
            continue
        bucket = timestamp.replace(second=0, microsecond=0)
        if bucket in buckets:
            buckets[bucket] += 1
    return jsonify(
        [{"time": moment.strftime("%H:%M"), "count": count} for moment, count in sorted(buckets.items())]
    )


@socketio.on("connect")
def on_connect():
    start_background_services()
    sid = request.sid
    with _recent_lock:
        history = list(_recent)
    # ``emit`` applies to the current client only. Broadcasting history here
    # would duplicate every old event for every already-connected visitor.
    for record in history:
        emit("attack", record, to=sid)


def main() -> None:
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8080"))
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    seed_demo = os.getenv("SEED_DEMO", "").lower() in {"1", "true", "yes"}
    if seed_demo:
        from tools.seed import seed_attacks

        seed_attacks(count=int(os.getenv("SEED_COUNT", "60")), log_path=LOG_PATH)
    start_background_services()
    logger.info("Dashboard listening on http://%s:%s", host, port)
    socketio.run(app, host=host, port=port, debug=False, allow_unsafe_werkzeug=True)


if __name__ == "__main__":
    main()
