"""Fake SSH honeypot.

Speaks a real SSH handshake (via paramiko) and records every
authentication attempt as a JSON line in the shared log file.

Usage:
    python -m honeypot.server --host 0.0.0.0 --port 2222
"""

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


def ensure_host_key() -> paramiko.RSAKey:
    """Generate (or load) a persistent SSH host key."""
    HOST_KEY_PATH.parent.mkdir(parents=True, exist_ok=True)
    if HOST_KEY_PATH.exists():
        return paramiko.RSAKey(filename=str(HOST_KEY_PATH))
    key = paramiko.RSAKey.generate(2048)
    key.write_private_key_file(str(HOST_KEY_PATH))
    return key


def log_attack(log_path: Path, record: dict) -> None:
    """Append one attack event as a JSON line."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


class FakeSSHServer(paramiko.ServerInterface):
    """Accepts every auth attempt and logs it as an attack event."""

    def __init__(self, log_path: Path, src_ip: str, src_port: int):
        self.log_path = log_path
        self.src_ip = src_ip
        self.src_port = src_port

    def check_auth_password(self, username: str, password: str):
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "src_ip": self.src_ip,
            "src_port": self.src_port,
            "username": username,
            "password": password,
            "success": False,
        }
        log_attack(self.log_path, record)
        return paramiko.AUTH_FAILED

    def check_channel_request(self, kind: str, chanid: int):
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def get_allowed_auths(self, username: str):
        return "password"


def handle_client(conn: socket.socket, addr, log_path: Path, host_key) -> None:
    transport = paramiko.Transport(conn)
    transport.local_version = BANNER
    transport.add_server_key(host_key)
    server = FakeSSHServer(log_path, addr[0], addr[1])
    try:
        transport.start_server(server=server)
        deadline = time.time() + 20
        while transport.is_active() and time.time() < deadline:
            time.sleep(0.5)
    except (EOFError, OSError, paramiko.SSHException):
        pass
    finally:
        transport.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Fake SSH honeypot")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=2222)
    parser.add_argument("--log", type=Path, default=LOG_PATH)
    args = parser.parse_args()

    host_key = ensure_host_key()
    print(f"[*] Honeypot listening on {args.host}:{args.port} (SSH)")
    print(f"[*] Attack log -> {args.log}")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((args.host, args.port))
        srv.listen(128)
        while True:
            conn, addr = srv.accept()
            threading.Thread(
                target=handle_client,
                args=(conn, addr, args.log, host_key),
                daemon=True,
            ).start()


if __name__ == "__main__":
    main()