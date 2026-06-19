import json
from pathlib import Path

from context_sieve.cli import run


def test_cli_returns_two_when_budget_is_exceeded(tmp_path: Path, capsys: object) -> None:
    path = tmp_path / "chunks.jsonl"
    rows = [
        {"id": "a", "text": "one two three four five"},
        {"id": "b", "text": "one two three four five"},
    ]
    path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")

    exit_code = run([str(path), "--fail-over", "10"])

    assert exit_code == 2


def test_cli_can_emit_json(tmp_path: Path, capsys: object) -> None:
    path = tmp_path / "chunks.jsonl"
    path.write_text(json.dumps({"id": "a", "text": "one two three four five"}), encoding="utf-8")

    exit_code = run([str(path), "--output", "json"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert json.loads(output)["total_chunks"] == 1
