"""Domain models for context analysis."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Chunk:
    """A single context chunk."""

    id: str
    text: str
    metadata: dict[str, object]


@dataclass(frozen=True, slots=True)
class DuplicateMember:
    """A duplicate chunk and its similarity to the cluster representative."""

    chunk: Chunk
    similarity: float
    estimated_tokens: int


@dataclass(frozen=True, slots=True)
class DuplicateCluster:
    """A group of chunks that carry substantially the same text."""

    representative: DuplicateMember
    duplicates: tuple[DuplicateMember, ...]
    kind: str

    @property
    def wasted_tokens(self) -> int:
        return sum(member.estimated_tokens for member in self.duplicates)


@dataclass(frozen=True, slots=True)
class AnalysisResult:
    """Summary and duplicate clusters for one scan."""

    total_chunks: int
    total_tokens: int
    redundant_chunks: int
    redundant_tokens: int
    clusters: tuple[DuplicateCluster, ...]

    @property
    def redundancy_ratio(self) -> float:
        if self.total_tokens == 0:
            return 0.0
        return self.redundant_tokens / self.total_tokens
