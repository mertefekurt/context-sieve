"""Command-line entry point."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from context_sieve import __version__
from context_sieve.analyzer import analyze_chunks
from context_sieve.loaders import InputError, load_paths
from context_sieve.report import render_json, render_terminal


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="context-sieve",
        description="Find duplicate chunks before they waste an LLM context window.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("paths", nargs="+", type=Path, help="input files to scan")
    parser.add_argument(
        "--input-format",
        choices=("jsonl", "text"),
        default="jsonl",
        help="input format (default: jsonl)",
    )
    parser.add_argument("--text-field", default="text", help="JSONL field containing chunk text")
    parser.add_argument("--id-field", default="id", help="JSONL field containing chunk ID")
    parser.add_argument(
        "--delimiter",
        default="\n---\n",
        help=r"text chunk delimiter (default: '\n---\n')",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.74,
        help="near-duplicate similarity threshold from 0 to 1 (default: 0.74)",
    )
    parser.add_argument(
        "--min-words",
        type=int,
        default=5,
        help="ignore shorter chunks when clustering (default: 5)",
    )
    parser.add_argument(
        "--output",
        choices=("terminal", "json"),
        default="terminal",
        help="report format (default: terminal)",
    )
    parser.add_argument(
        "--fail-over",
        type=float,
        metavar="PERCENT",
        help="exit 2 when estimated token waste exceeds this percentage",
    )
    return parser


def run(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.fail_over is not None and not 0.0 <= args.fail_over <= 100.0:
        print("error: --fail-over must be between 0 and 100", file=sys.stderr)
        return 1

    try:
        chunks = load_paths(
            args.paths,
            input_format=args.input_format,
            text_field=args.text_field,
            id_field=args.id_field,
            delimiter=args.delimiter,
        )
        result = analyze_chunks(chunks, threshold=args.threshold, min_words=args.min_words)
    except (InputError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    renderer = render_json if args.output == "json" else render_terminal
    print(renderer(result))

    if args.fail_over is not None and result.redundancy_ratio * 100 > args.fail_over:
        return 2
    return 0


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
