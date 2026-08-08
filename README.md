<div align="center">
<img src="assets/logo.svg" width="120" height="120" alt="SecureSync logo">

# SecureSync

**Encrypted peer-to-peer file synchronization engine.**

[![CI](https://github.com/<org>/securesync/actions/workflows/ci.yml/badge.svg)](.github/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue)]()
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Contributor Covenant](https://img.shields.io/badge/Contributor%20Covenant-inspired-4baaaa.svg)](CODE_OF_CONDUCT.md)
[![Status](https://img.shields.io/badge/status-Phase_10_%E2%80%94_production_runtime-green)]()

</div>

> ✅ **Project status:** Phases 1 through 10 are fully implemented.
> SecureSync now features a production-ready runtime, SQLite-backed
> metadata storage, end-to-end encryption, and an orchestration layer
> for automated peer-to-peer synchronization. See
> [ROADMAP.md](ROADMAP.md) for the implementation history.

---

## Table of Contents

- [What is SecureSync?](#what-is-securesync)
- [Architecture](#architecture)
- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Documentation](#documentation)
- [Benchmarks](#benchmarks)
- [Roadmap](#roadmap)
- [FAQ](#faq)
- [Contributing](#contributing)
- [Security](#security)
- [Community](#community)
- [License](#license)

## What is SecureSync?

SecureSync is a peer-to-peer file synchronization engine: devices discover
each other on the network, establish an authenticated end-to-end encrypted
channel, and synchronize only the parts of files that actually changed. No
central server holds your data.

## Architecture

SecureSync is built with Clean Architecture — domain logic is fully isolated
from infrastructure (filesystem, network, database), which keeps the core
sync/conflict-resolution logic testable and every adapter (transport, cipher,
discovery mechanism) independently swappable.

Full write-up: [docs/architecture.md](docs/architecture.md)

```mermaid
flowchart LR
    A[Filesystem Watcher] --> B[Chunk Engine]
    B --> C[Delta Sync]
    C --> D[Transfer Engine]
    D <--> E[Peer Discovery]
    D --> F[End-to-End Encryption]
    C --> G[Conflict Resolution]
    C --> H[(Metadata DB)]
```

## Features

- [x] Real-time filesystem watching (create/modify/delete/rename/move)
- [x] Streaming, bounded-memory chunking + SHA-256 hashing
- [x] Delta synchronization: content-hash comparison against a recorded baseline
- [x] Peer discovery (mDNS)
- [x] Streamed transfers with binary wire protocol
- [x] End-to-end encryption: X25519 key exchange, AES-256-GCM / ChaCha20-Poly1305
- [x] Conflict resolution with version vectors and pluggable strategies
- [x] SQLite-backed metadata store (files, chunks, version history)
- [x] Synchronization Orchestrator with state machine and lifecycle control
- [x] YAML + environment variable configuration and production bootstrap

## Installation

```bash
git clone https://github.com/<org>/securesync.git
cd securesync
pip install -e ".[dev]"
```

## Quick Start

```bash
# Start the synchronization engine with a config file
python -m securesync.main config.yaml
```

## Configuration

The YAML schema and environment variable overrides are fully documented in
[docs/configuration.md](docs/configuration.md).

## Documentation

| Doc | Covers |
|---|---|
| [docs/architecture.md](docs/architecture.md) | Clean Architecture layers, SOLID, design patterns, tech decisions, diagrams |
| [docs/networking.md](docs/networking.md) | Peer discovery, topology, connection lifecycle |
| [docs/protocol.md](docs/protocol.md) | Binary wire protocol: header layout, packet types, handshake |
| [docs/security.md](docs/security.md) | Cryptographic design and full threat model |
| [docs/performance.md](docs/performance.md) | Benchmark methodology and metrics tracked |
| [docs/development.md](docs/development.md) | Local dev setup, testing conventions |
| [docs/deployment.md](docs/deployment.md) | Docker, docker-compose, systemd, ports |
| [docs/configuration.md](docs/configuration.md) | YAML schema, environment variables, hot reload |
| [docs/troubleshooting.md](docs/troubleshooting.md) | Common issues and diagnostics |
| [docs/adr/](docs/adr/) | Architecture Decision Records |

## Benchmarks

Benchmarks for chunking, hashing, encryption, and networking are implemented — see
[benchmarks/](benchmarks/). Methodology is defined in [docs/performance.md](docs/performance.md).

## Roadmap

See [ROADMAP.md](ROADMAP.md) for the full phase-by-phase plan.

## FAQ

**Why not just use Syncthing?**
SecureSync is an educational, ground-up implementation built to demonstrate
architecture, networking, and cryptography engineering practices.

**Is the cryptography audited?**
SecureSync only uses well-established primitives from the audited `cryptography`
(pyca) library. The *composition* of those primitives into a protocol is not
independently audited.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for the development workflow,
coding standards, and commit conventions.

## Security

See [SECURITY.md](SECURITY.md) for how to privately report a
vulnerability, and [docs/security.md](docs/security.md) for the full
cryptographic design and threat model.

## Community

- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Issue templates](.github/ISSUE_TEMPLATE/) — bug reports and feature requests
- [Pull request template](.github/PULL_REQUEST_TEMPLATE.md)
- [Architecture Decision Records](docs/adr/) — the "why" behind every major decision

## License

[MIT](LICENSE)
