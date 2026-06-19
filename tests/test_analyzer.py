import pytest

from context_sieve.analyzer import analyze_chunks
from context_sieve.models import Chunk


def chunk(identifier: str, text: str) -> Chunk:
    return Chunk(id=identifier, text=text, metadata={})


def test_exact_duplicates_form_cluster() -> None:
    result = analyze_chunks(
        [
            chunk("a", "Vector databases store embeddings for semantic retrieval."),
            chunk("b", " vector databases STORE embeddings for semantic retrieval. "),
        ]
    )

    assert result.redundant_chunks == 1
    assert result.clusters[0].kind == "exact"


def test_near_duplicates_form_cluster() -> None:
    result = analyze_chunks(
        [
            chunk("a", "The service validates structured model output against a JSON schema."),
            chunk("b", "The service validates structured LLM output against the JSON schema."),
        ],
        threshold=0.70,
    )

    assert result.redundant_chunks == 1
    assert result.clusters[0].kind == "near"


def test_short_chunks_are_ignored() -> None:
    result = analyze_chunks(
        [chunk("a", "same tiny text"), chunk("b", "same tiny text")],
        min_words=5,
    )

    assert result.clusters == ()


def test_longest_chunk_becomes_representative() -> None:
    result = analyze_chunks(
        [
            chunk("short", "Agents call tools using validated structured input."),
            chunk(
                "long",
                "Agents call tools using validated structured input with explicit schemas.",
            ),
        ],
        threshold=0.60,
    )

    assert result.clusters[0].representative.chunk.id == "long"


def test_redundancy_ratio_uses_estimated_tokens() -> None:
    result = analyze_chunks(
        [
            chunk("a", "one two three four five"),
            chunk("b", "one two three four five"),
            chunk("c", "unique context remains useful here"),
        ]
    )

    assert result.redundant_tokens == 5
    assert result.redundancy_ratio == pytest.approx(5 / 15)


def test_invalid_threshold_is_rejected() -> None:
    with pytest.raises(ValueError, match="threshold"):
        analyze_chunks([], threshold=1.1)
