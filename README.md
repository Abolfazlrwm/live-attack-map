# 🗺️ Live Attack Map

[![CI](https://github.com/Abolfazlrwm/live-attack-map/actions/workflows/ci.yml/badge.svg)](https://github.com/Abolfazlrwm/live-attack-map/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](pyproject.toml)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED.svg)](docker-compose.yml)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

> A fake SSH honeypot that logs **real** brute-force attempts from the internet
> and streams them to a **real-time animated world map** dashboard.

## ✨ Features

- **Real SSH handshake** — speaks the genuine SSH protocol (paramiko), so real
  scanners and botnets treat it like any other server
- **Credential harvesting** — every username/password attempt is captured to a JSON log
- **Live geolocation** — attacker IPs mapped to countries (ip-api, cached)
- **Real-time dashboard** — WebSocket streaming with animated attack lines
- **Statistics panel** — top countries, usernames, passwords, attacks per minute
- **Demo mode** — seed realistic traffic instantly for testing and screenshots
- **One-command deploy** — `docker compose up`

## 🏗️ Architecture

```mermaid
graph LR
    A[Internet scanners] -->|SSH attempt| B(Fake SSH honeypot)
    B -->|JSON line| C[(attacks.jsonl)]
    C --> D[Dashboard backend]
    D -->|WebSocket| E[Leaflet map + stats panel]
    D -->|REST| F[/api/attacks/]
