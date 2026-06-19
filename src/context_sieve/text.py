"""Text normalization and fingerprinting primitives."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from collections import Counter

TOKEN_PATTERN = re.compile(r"\w+|[^\w\s]", re.UNICODE)
WORD_PATTERN = re.compile(r"\w+", re.UNICODE)


def normalize(text: str) -> str:
    """Normalize text for stable exact comparisons."""
    normalized = unicodedata.normalize("NFKC", text).casefold()
    return " ".join(normalized.split())


def words(text: str) -> list[str]:
    """Return normalized word tokens."""
    return WORD_PATTERN.findall(normalize(text))


def estimate_tokens(text: str) -> int:
    """Estimate model tokens without binding the tool to one tokenizer."""
    return len(TOKEN_PATTERN.findall(text))


def simhash(text: str, shingle_size: int = 2) -> int:
    """Build a deterministic 64-bit SimHash from word shingles."""
    tokens = words(text)
    if not tokens:
        return 0

    size = min(shingle_size, len(tokens))
    shingles = Counter(
        " ".join(tokens[index : index + size]) for index in range(len(tokens) - size + 1)
    )
    vector = [0] * 64

    for shingle, weight in shingles.items():
        digest = hashlib.blake2b(shingle.encode("utf-8"), digest_size=8).digest()
        value = int.from_bytes(digest, byteorder="big")
        for bit in range(64):
            vector[bit] += weight if value & (1 << bit) else -weight

    fingerprint = 0
    for bit, score in enumerate(vector):
        if score >= 0:
            fingerprint |= 1 << bit
    return fingerprint


def fingerprint_similarity(left: int, right: int) -> float:
    """Return similarity in the inclusive range 0..1."""
    distance = (left ^ right).bit_count()
    return 1.0 - (distance / 64)
