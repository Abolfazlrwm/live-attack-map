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

🚀 Quick Start — copy everything below
Docker (fastest) — one line, one terminal
bash



git clone https://github.com/Abolfazlrwm/live-attack-map.git && cd live-attack-map && docker compose up --build
Manual — Windows PowerShell (one terminal, everything)
powershell



git clone https://github.com/Abolfazlrwm/live-attack-map.git
cd live-attack-map
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Start-Process python -ArgumentList "-m","honeypot.server","--port","2222"
Start-Process python -ArgumentList "-m","dashboard.app"
Start-Sleep -Seconds 2
python tools/seed.py --count 60
Manual — Linux / macOS (one terminal, everything)
bash



git clone https://github.com/Abolfazlrwm/live-attack-map.git
cd live-attack-map
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m honeypot.server --port 2222 &
python -m dashboard.app &
python tools/seed.py --count 60
Then open http://localhost:8080 — the map fills with animated attacks from cities all over the world within seconds.

Test everything (one block)
bash



pip install pytest ruff && ruff check . && pytest -v
Expected result: 5 tests passed ✅

⚙️ Configuration (environment variables)


Variable	Default	Description
PORT	8080	Dashboard port
LOG_PATH	logs/attacks.jsonl	Shared attack log file
TARGET_LAT	35.6892	Map target marker latitude
TARGET_LON	51.3890	Map target marker longitude
TARGET_LABEL	Honeypot	Target marker label
Example:

bash



TARGET_LAT=48.8566 TARGET_LON=2.3522 TARGET_LABEL=Paris python -m dashboard.app
📁 Project Structure



live-attack-map/
├── .github/workflows/ci.yml   # CI: lint + tests (GitHub Actions)
├── honeypot/                  # Fake SSH server (paramiko)
│   └── server.py
├── dashboard/                 # Flask + SocketIO backend
│   ├── app.py                 # Web server + WebSocket streaming
│   ├── geo.py                 # IP geolocation (ip-api, cached)
│   └── templates/index.html   # Leaflet map + stats panel
├── tools/
│   └── seed.py                # Demo attack generator
├── tests/                     # pytest suite
├── Dockerfile
├── docker-compose.yml
├── Makefile
└── pyproject.toml
🛠️ Tech Stack
Python 3.10+ — Flask, Flask-SocketIO, Paramiko, Requests
Leaflet.js — interactive dark world map
WebSocket (Socket.IO) — real-time event streaming
Docker & docker-compose — containerized deployment
GitHub Actions — automated lint + test pipeline
⚠️ Responsible Use
This is a defensive security / threat intelligence tool. Run it only on infrastructure you own. The honeypot never grants access — it only observes and logs. Attack data may contain IPs of innocent parties; use it ethically and anonymize before sharing.

🗺️ Roadmap
 Telegram / email alerting on new attacks
 CSV / JSON export of attack data
 Additional fake services (HTTP, FTP, Telnet)
 Attack origin heatmap (time-of-day analysis)
 Login attempt timeline chart
🤝 Contributing
Contributions are welcome! See CONTRIBUTING.md [blocked] for guidelines, and please run ruff check . and pytest -v before opening a PR.

📄 License
MIT [blocked] © 2026 Abolfazlrwm
