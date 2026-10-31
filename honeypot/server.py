"""Fake SSH honeypot.

Speaks a real SSH handshake (via paramiko) and records every authentication
attempt as a JSON line in the shared log file.

Safety boundary: this server never opens a shell, forwards a channel, executes
a command, reads a host file, or makes an outbound request on behalf of an
attacker. It only performs the SSH handshake and records credential attempts.

Usage:
    python -m honeypot.server --host 0.0.0.0 --port 2222
"""

from __future__ import annotations

import argparse
import json
import socket
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

import paramiko

HOST_KEY_PATH = Path("data/ssh_host_rsa_key")
LOG_PATH = Path("logs/attacks.jsonl")
BANNER = "SSH-2.0-OpenSSH_7.6p1 Ubuntu-4ubuntu0.3"
MAX_USERNAME_LENGTH = 256
MAX_PASSWORD_LENGTH = 1024

_log_lock = threading.Lock()


def ensure_host_key(path: Path = HOST_KEY_PATH) -> paramiko.RSAKey:
    """Generate (or load) a persistent SSH host key."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return paramiko.RSAKey(filename=str(path))
    key = paramiko.RSAKey.generate(2048)
    key.write_private_key_file(str(path))
    return key


def log_attack(log_path: Path, record: dict) -> None:
    """Append one attack event as a JSON line, serializing concurrent writers."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, ensure_ascii=False) + "\n"
    with _log_lock, log_path.open("a", encoding="utf-8") as handle:
        handle.write(line)


class ConnectionLimiter:
    """Non-blocking concurrency cap backed by a bounded semaphore."""

    def __init__(self, maximum: int) -> None:
        if maximum < 1:
            raise ValueError("maximum must be at least 1")
        self.maximum = maximum
        self._semaphore = threading.BoundedSemaphore(maximum)

    def acquire(self) -> bool:
        return self._semaphore.acquire(blocking=False)

    def release(self) -> None:
        self._semaphore.release()


class FakeSSHServer(paramiko.ServerInterface):
    """Rejects every auth attempt while recording it as an attack event."""

    def __init__(self, log_path: Path, src_ip: str, src_port: int, *, max_attempts: int = 6):
        self.log_path = log_path
        self.src_ip = src_ip
        self.src_port = src_port
        self.max_attempts = max_attempts
        self.attempts = 0

    def check_auth_password(self, username: str, password: str):
        if self.attempts >= self.max_attempts:
            return paramiko.AUTH_FAILED
        self.attempts += 1
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "src_ip": self.src_ip,
            "src_port": self.src_port,
            "username": str(username)[:MAX_USERNAME_LENGTH],
            "password": str(password)[:MAX_PASSWORD_LENGTH],
            "success": False,
        }
        log_attack(self.log_path, record)
        return paramiko.AUTH_FAILED

    def check_channel_request(self, kind: str, chanid: int):
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def get_allowed_auths(self, username: str):
        return "password"


def handle_client(
    conn: socket.socket,
    addr: tuple[str, int],
    log_path: Path,
    host_key: paramiko.RSAKey,
    *,
    timeout: float = 20.0,
) -> None:
    transport = paramiko.Transport(conn)
    transport.local_version = BANNER
    transport.add_server_key(host_key)
    transport.banner_timeout = timeout
    transport.auth_timeout = timeout
    transport.channel_timeout = timeout
    server = FakeSSHServer(log_path, addr[0], addr[1])
    try:
        transport.start_server(server=server)
        deadline = time.monotonic() + timeout
        while transport.is_active() and time.monotonic() < deadline:
            time.sleep(0.25)
    except (EOFError, OSError, paramiko.SSHException):
        pass
    finally:
        transport.close()


def _serve_client(
    conn: socket.socket,
    addr: tuple[str, int],
    log_path: Path,
    host_key: paramiko.RSAKey,
    limiter: ConnectionLimiter,
    timeout: float,
) -> None:
    try:
        handle_client(conn, addr, log_path, host_key, timeout=timeout)
    finally:
        limiter.release()


def main() -> None:
    parser = argparse.ArgumentParser(description="Fake SSH honeypot")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=2222)
    parser.add_argument("--log", type=Path, default=LOG_PATH)
    parser.add_argument("--host-key", type=Path, default=HOST_KEY_PATH)
    parser.add_argument("--max-connections", type=int, default=50)
    parser.add_argument("--timeout", type=float, default=20.0)
    args = parser.parse_args()

    host_key = ensure_host_key(args.host_key)
    limiter = ConnectionLimiter(args.max_connections)
    print(f"[*] Honeypot listening on {args.host}:{args.port} (SSH)")
    print(f"[*] Attack log -> {args.log}")
    print(f"[*] Max concurrent connections: {args.max_connections}")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((args.host, args.port))
        server.listen(128)
        try:
            while True:
                conn, addr = server.accept()
                if not limiter.acquire():
                    conn.close()
                    continue
                threading.Thread(
                    target=_serve_client,
                    args=(conn, addr, args.log, host_key, limiter, args.timeout),
                    daemon=True,
                    name=f"ssh-{addr[0]}",
                ).start()
        except KeyboardInterrupt:
            print("\n[*] Shutting down honeypot")


if __name__ == "__main__":
    main()
