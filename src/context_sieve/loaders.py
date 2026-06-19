"""Input loaders for common context-bundle formats."""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path

from context_sieve.models import Chunk


class InputError(ValueError):
    """Raised when context input cannot be parsed safely."""


def load_jsonl(path: Path, text_field: str, id_field: str | None) -> list[Chunk]:
    """Load one chunk per JSONL record."""
    chunks: list[Chunk] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise InputError(f"cannot read {path}: {exc}") from exc

    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise InputError(f"{path}:{line_number}: invalid JSON: {exc.msg}") from exc
        if not isinstance(record, dict):
            raise InputError(f"{path}:{line_number}: expected a JSON object")

        text = record.get(text_field)
        if not isinstance(text, str):
            raise InputError(f"{path}:{line_number}: field {text_field!r} must be a string")

        raw_id = record.get(id_field) if id_field else None
        chunk_id = str(raw_id) if raw_id is not None else str(line_number)
        metadata = {
            key: value for key, value in record.items() if key not in {text_field, id_field}
        }
        chunks.append(Chunk(id=chunk_id, text=text, metadata=metadata))

    return chunks


def load_text(path: Path, delimiter: str) -> list[Chunk]:
    """Load chunks from a delimited UTF-8 text file."""
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise InputError(f"cannot read {path}: {exc}") from exc

    parts = [part.strip() for part in content.split(delimiter)]
    return [
        Chunk(id=str(index), text=part, metadata={})
        for index, part in enumerate(parts, start=1)
        if part
    ]


def load_paths(
    paths: Iterable[Path],
    *,
    input_format: str,
    text_field: str,
    id_field: str | None,
    delimiter: str,
) -> list[Chunk]:
    """Load and combine chunks from multiple paths."""
    chunks: list[Chunk] = []
    for path in paths:
        loaded = (
            load_jsonl(path, text_field=text_field, id_field=id_field)
            if input_format == "jsonl"
            else load_text(path, delimiter=delimiter)
        )
        prefix = path.name
        chunks.extend(
            Chunk(id=f"{prefix}:{chunk.id}", text=chunk.text, metadata=chunk.metadata)
            for chunk in loaded
        )
    return chunks
