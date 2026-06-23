"""Command-line interface for logslice.

Usage:
    logslice <trace_id> service-a.log service-b.log gateway.log
    logslice abc123 logs/*.log
    logslice abc123 logs/*.log --json     # machine-readable output
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .core import build_timeline, timeline_span_seconds


def _load(paths: list[str]) -> dict[str, list[str]]:
    sources: dict[str, list[str]] = {}
    for p in paths:
        path = Path(p)
        try:
            sources[path.name] = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError as exc:
            print(f"warning: could not read {p}: {exc}", file=sys.stderr)
    return sources


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="logslice",
        description="Reconstruct one request's journey across many service logs by trace id.",
    )
    parser.add_argument("trace_id", help="The trace / correlation id to follow.")
    parser.add_argument("logs", nargs="+", help="Log files to search.")
    parser.add_argument("--json", action="store_true", dest="as_json",
                        help="Emit the timeline as JSON.")
    args = parser.parse_args(argv)

    sources = _load(args.logs)
    timeline = build_timeline(sources, args.trace_id)

    if not timeline:
        print(f"No log lines found for trace id '{args.trace_id}'.")
        return 1

    if args.as_json:
        print(json.dumps([
            {"timestamp": e.ts_display, "source": e.source, "message": e.raw}
            for e in timeline
        ], indent=2))
        return 0

    span = timeline_span_seconds(timeline)
    print(f"\nTimeline for trace '{args.trace_id}'  "
          f"({len(timeline)} events across {len(sources)} sources"
          + (f", span {span:.3f}s" if span is not None else "") + ")\n")

    # Width-align the source column for readability.
    width = max((len(e.source) for e in timeline), default=0)
    for e in timeline:
        print(f"  {e.ts_display:<32} {e.source:<{width}}  {e.raw}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
