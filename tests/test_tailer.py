from __future__ import annotations

import json

from dashboard.tailer import LogTailer


def test_tailer_waits_for_complete_line(tmp_path):
    path = tmp_path / "attacks.jsonl"
    path.write_text('{"n": 1}', encoding="utf-8")
    tailer = LogTailer(path, start_at_end=False)

    assert tailer.read_new_lines() == []

    with path.open("a", encoding="utf-8") as handle:
        handle.write('\n{"n": 2}\n{"n": 3}')
    lines = tailer.read_new_lines()
    assert [json.loads(line)["n"] for line in lines] == [1, 2]
    assert tailer.read_new_lines() == []

    with path.open("a", encoding="utf-8") as handle:
        handle.write("\n")
    assert [json.loads(line)["n"] for line in tailer.read_new_lines()] == [3]


def test_tailer_resets_after_rotation(tmp_path):
    path = tmp_path / "attacks.jsonl"
    path.write_text('{"old": true}\n', encoding="utf-8")
    tailer = LogTailer(path, start_at_end=False)
    assert len(tailer.read_new_lines()) == 1

    rotated = tmp_path / "attacks.jsonl.1"
    path.replace(rotated)
    path.write_text('{"new": true}\n', encoding="utf-8")

    lines = tailer.read_new_lines()
    assert len(lines) == 1
    assert json.loads(lines[0]) == {"new": True}


def test_tailer_resets_after_truncation(tmp_path):
    path = tmp_path / "attacks.jsonl"
    path.write_text('{"old": true}\n', encoding="utf-8")
    tailer = LogTailer(path, start_at_end=False)
    tailer.read_new_lines()

    path.write_text('{"n": 1}\n', encoding="utf-8")
    lines = tailer.read_new_lines()
    assert [json.loads(line) for line in lines] == [{"n": 1}]


def test_tailer_start_at_end_skips_existing(tmp_path):
    path = tmp_path / "attacks.jsonl"
    path.write_text('{"old": true}\n', encoding="utf-8")
    tailer = LogTailer(path, start_at_end=True)
    assert tailer.read_new_lines() == []
    with path.open("a", encoding="utf-8") as handle:
        handle.write('{"new": true}\n')
    assert [json.loads(line) for line in tailer.read_new_lines()] == [{"new": True}]
