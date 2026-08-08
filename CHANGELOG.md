# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [1.0.0] - 2026-08-08

### Added
- Fake SSH honeypot (paramiko) that logs every credential attempt
- Real-time dashboard with Leaflet attack map and WebSocket streaming
- IP geolocation with caching (ip-api)
- Demo seeding tool for local testing and screenshots
- Docker + docker-compose deployment
- CI pipeline (GitHub Actions): ruff lint + pytest
- Unit tests for honeypot, geolocation and dashboard API