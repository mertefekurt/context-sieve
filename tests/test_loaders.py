import json
from pathlib import Path

import pytest

from context_sieve.loaders import InputError, load_jsonl, load_text


def test_load_jsonl_preserves_metadata(tmp_path: Path) -> None:
    path = tmp_path / "chunks.jsonl"
    path.write_text(
        json.dumps({"id": "a", "content": "hello", "source": "manual"}) + "\n",
        encoding="utf-8",
    )

    chunks = load_jsonl(path, text_field="content", id_field="id")

    assert chunks[0].id == "a"
    assert chunks[0].metadata == {"source": "manual"}


def test_load_jsonl_reports_line_number(tmp_path: Path) -> None:
    path = tmp_path / "broken.jsonl"
    path.write_text('{"text": "ok"}\nnot-json\n', encoding="utf-8")

    with pytest.raises(InputError, match=r"broken\.jsonl:2"):
        load_jsonl(path, text_field="text", id_field="id")


def test_load_text_splits_chunks_and_skips_empty_parts(tmp_path: Path) -> None:
    path = tmp_path / "chunks.txt"
    path.write_text("first\n---\n\n---\nsecond", encoding="utf-8")

    chunks = load_text(path, delimiter="\n---\n")

    assert [chunk.text for chunk in chunks] == ["first", "second"]
