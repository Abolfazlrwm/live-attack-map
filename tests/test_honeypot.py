from __future__ import annotations

import json
from pathlib import Path

import paramiko

from honeypot.server import ConnectionLimiter, FakeSSHServer, log_attack


def test_log_attack_writes_json_line(tmp_path):
    log_path = tmp_path / "attacks.jsonl"
    record = {"src_ip": "1.2.3.4", "username": "root", "password": "toor"}
    log_attack(log_path, record)
    lines = log_path.read_text().strip().splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["username"] == "root"


def test_concurrent_connection_limit():
    limiter = ConnectionLimiter(2)
    assert limiter.acquire()
    assert limiter.acquire()
    assert not limiter.acquire()
    limiter.release()
    assert limiter.acquire()
    limiter.release()
    limiter.release()


def test_attempt_count_is_capped(tmp_path):
    log_path = tmp_path / "attacks.jsonl"
    server = FakeSSHServer(log_path, "8.8.8.8", 2222, max_attempts=3)
    for _ in range(5):
        assert server.check_auth_password("root", "toor") == paramiko.AUTH_FAILED
    assert len(log_path.read_text().strip().splitlines()) == 3
    assert server.attempts == 3


def test_truncates_oversized_credentials(tmp_path):
    log_path = tmp_path / "attacks.jsonl"
    server = FakeSSHServer(log_path, "8.8.8.8", 2222)
    server.check_auth_password("u" * 1000, "p" * 5000)
    record = json.loads(log_path.read_text().strip())
    assert len(record["username"]) == 256
    assert len(record["password"]) == 1024


def test_channel_requests_are_denied():
    server = FakeSSHServer(Path("unused.jsonl"), "8.8.8.8", 2222)
    assert server.check_channel_request("session", 0) != 0
    assert server.get_allowed_auths("root") == "password"
