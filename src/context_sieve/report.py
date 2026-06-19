"""Terminal and JSON report rendering."""

from __future__ import annotations

import json
from dataclasses import asdict

from context_sieve.models import AnalysisResult


def render_terminal(result: AnalysisResult) -> str:
    """Render a compact human-readable report."""
    lines = [
        "context-sieve scan",
        (
            f"{result.total_chunks} chunks · ~{result.total_tokens} tokens · "
            f"{result.redundant_chunks} redundant chunks"
        ),
        (
            f"estimated waste: ~{result.redundant_tokens} tokens "
            f"({result.redundancy_ratio:.1%} of input)"
        ),
    ]

    if not result.clusters:
        lines.extend(["", "No duplicate clusters found."])
        return "\n".join(lines)

    for number, cluster in enumerate(result.clusters, start=1):
        lines.extend(
            [
                "",
                (
                    f"[{number}] {cluster.kind} cluster · keep "
                    f"{cluster.representative.chunk.id} · save ~{cluster.wasted_tokens} tokens"
                ),
            ]
        )
        for duplicate in cluster.duplicates:
            lines.append(
                f"    remove {duplicate.chunk.id} "
                f"(similarity {duplicate.similarity:.1%}, ~{duplicate.estimated_tokens} tokens)"
            )
    return "\n".join(lines)


def render_json(result: AnalysisResult) -> str:
    """Render a machine-readable report."""
    payload = asdict(result)
    payload["redundancy_ratio"] = result.redundancy_ratio
    return json.dumps(payload, indent=2, ensure_ascii=False)
