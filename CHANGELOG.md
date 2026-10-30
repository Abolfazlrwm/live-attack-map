# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [1.0.1] - 2026-10-30

### Fixed
- The dashboard now calls `socketio.run()` and stays running instead of exiting
  immediately.
- Attacker-controlled usernames, passwords, IPs, and country names are rendered
  with `textContent`/DOM nodes; the previous `innerHTML` sinks are gone.
- The map target is loaded from `/api/config`, so `TARGET_LAT`, `TARGET_LON`,
  and `TARGET_LABEL` now affect the UI.
- History replay is emitted only to the newly connected Socket.IO client
  instead of being broadcast to every visitor again.
- The log tailer reads bytes, waits for newline-terminated lines, and recovers
  from rotation and truncation without skipping records.
- Geolocation runs in a background worker and skips private, loopback,
  link-local, and reserved addresses.
- `SECRET_KEY` is never the hard-coded `change-me` value, and wildcard CORS is
  no longer enabled by default.
- The honeypot caps concurrent connections and enforces banner, auth, channel,
  and session timeouts.

### Added
- `/healthz` endpoint with version, uptime, and buffered-event count.
- `/api/config` endpoint for target marker configuration.
- Configurable demo seeding in Docker (`SEED_DEMO`, `SEED_COUNT`).
- Regression tests for XSS sinks, per-client history, partial lines, rotation,
  reserved IPs, geolocation caching, and connection limits.

## [1.0.0] - 2026-08-08

### Added
- Fake SSH honeypot (paramiko) that logs every credential attempt
- Real-time dashboard with Leaflet attack map and WebSocket streaming
- IP geolocation with caching (ip-api)
- Demo seeding tool for local testing and screenshots
- Docker + docker-compose deployment
- CI pipeline (GitHub Actions): ruff lint + pytest
- Unit tests for honeypot, geolocation and dashboard API