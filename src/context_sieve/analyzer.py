"""Duplicate clustering for context chunks."""

from __future__ import annotations

from collections import defaultdict

from context_sieve.models import (
    AnalysisResult,
    Chunk,
    DuplicateCluster,
    DuplicateMember,
)
from context_sieve.text import estimate_tokens, fingerprint_similarity, normalize, simhash


class _DisjointSet:
    def __init__(self, size: int) -> None:
        self.parent = list(range(size))

    def find(self, item: int) -> int:
        while self.parent[item] != item:
            self.parent[item] = self.parent[self.parent[item]]
            item = self.parent[item]
        return item

    def union(self, left: int, right: int) -> None:
        left_root = self.find(left)
        right_root = self.find(right)
        if left_root != right_root:
            self.parent[right_root] = left_root


def analyze_chunks(
    chunks: list[Chunk],
    *,
    threshold: float = 0.74,
    min_words: int = 5,
) -> AnalysisResult:
    """Find exact and near-duplicate clusters."""
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("threshold must be between 0 and 1")
    if min_words < 1:
        raise ValueError("min_words must be at least 1")

    token_counts = [estimate_tokens(chunk.text) for chunk in chunks]
    normalized = [normalize(chunk.text) for chunk in chunks]
    fingerprints = [simhash(chunk.text) for chunk in chunks]
    word_counts = [len(value.split()) for value in normalized]
    groups = _DisjointSet(len(chunks))

    for left in range(len(chunks)):
        if word_counts[left] < min_words:
            continue
        for right in range(left + 1, len(chunks)):
            if word_counts[right] < min_words:
                continue
            if normalized[left] == normalized[right]:
                groups.union(left, right)
                continue
            similarity = fingerprint_similarity(fingerprints[left], fingerprints[right])
            if similarity >= threshold:
                groups.union(left, right)

    components: dict[int, list[int]] = defaultdict(list)
    for index in range(len(chunks)):
        components[groups.find(index)].append(index)

    clusters: list[DuplicateCluster] = []
    for indices in components.values():
        if len(indices) < 2:
            continue

        representative_index = max(indices, key=lambda index: (token_counts[index], -index))
        representative_fingerprint = fingerprints[representative_index]
        members = []
        for index in indices:
            similarity = (
                1.0
                if normalized[index] == normalized[representative_index]
                else fingerprint_similarity(fingerprints[index], representative_fingerprint)
            )
            members.append(
                DuplicateMember(
                    chunk=chunks[index],
                    similarity=similarity,
                    estimated_tokens=token_counts[index],
                )
            )

        representative = next(
            member for member in members if member.chunk is chunks[representative_index]
        )
        duplicates = tuple(
            sorted(
                (member for member in members if member is not representative),
                key=lambda member: (-member.similarity, member.chunk.id),
            )
        )
        kind = "exact" if all(member.similarity == 1.0 for member in duplicates) else "near"
        clusters.append(
            DuplicateCluster(
                representative=representative,
                duplicates=duplicates,
                kind=kind,
            )
        )

    ordered_clusters = tuple(
        sorted(
            clusters,
            key=lambda cluster: (-cluster.wasted_tokens, cluster.representative.chunk.id),
        )
    )
    redundant_tokens = sum(cluster.wasted_tokens for cluster in ordered_clusters)
    redundant_chunks = sum(len(cluster.duplicates) for cluster in ordered_clusters)
    return AnalysisResult(
        total_chunks=len(chunks),
        total_tokens=sum(token_counts),
        redundant_chunks=redundant_chunks,
        redundant_tokens=redundant_tokens,
        clusters=ordered_clusters,
    )
