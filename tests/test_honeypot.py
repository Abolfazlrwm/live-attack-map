import json

from honeypot.server import log_attack


def test_log_attack_writes_json_line(tmp_path):
    log_path = tmp_path / "attacks.jsonl"
    record = {"src_ip": "1.2.3.4", "username": "root", "password": "toor"}
    log_attack(log_path, record)
    lines = log_path.read_text().strip().splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["username"] == "root"
