"""Core log-correlation engine.

Given many log files from different services, extract every line that carries a
given trace/correlation id, parse out a timestamp and source, and merge them
into one chronologically-ordered timeline.

Pure functions over strings/paths so the logic is fully unit-testable.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone

# ISO-8601-ish timestamp, e.g. 2024-01-01T12:00:00.123Z or with space + offset.
_TS_RE = re.compile(
    r"(\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:[.,]\d{1,9})?(?:Z|[+-]\d{2}:?\d{2})?)"
)


@dataclass
class Event:
    """One correlated log line on the timeline."""
    timestamp: datetime | None
    source: str          # which service/file it came from
    raw: str             # the original line (trimmed)

    @property
    def ts_display(self) -> str:
        return self.timestamp.isoformat() if self.timestamp else "??? (no timestamp)"


def parse_timestamp(line: str) -> datetime | None:
    """Best-effort timestamp extraction. Returns a timezone-aware UTC datetime
    when an offset is present, else a naive datetime. None if not found."""
    match = _TS_RE.search(line)
    if not match:
        return None
    raw = match.group(1).replace(",", ".").replace(" ", "T")
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(raw)
    except ValueError:
        return None
    # Normalize aware datetimes to UTC so cross-service ordering is correct.
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc)
    return dt


def line_matches(line: str, trace_id: str) -> bool:
    """True if the line references the trace id.

    Handles both plain substring matches and JSON logs where the id may live in
    a field like trace_id / traceId / correlation_id.
    """
    if trace_id in line:
        return True
    stripped = line.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        try:
            obj = json.loads(stripped)
        except json.JSONDecodeError:
            return False
        for key in ("trace_id", "traceId", "correlation_id", "correlationId", "traceID"):
            if str(obj.get(key, "")) == trace_id:
                return True
    return False


def extract_events(lines: list[str], trace_id: str, source: str) -> list[Event]:
    """Pull every line that references `trace_id` from one source."""
    events = []
    for line in lines:
        line = line.rstrip("\n")
        if line.strip() and line_matches(line, trace_id):
            events.append(Event(parse_timestamp(line), source, line.strip()))
    return events


def build_timeline(sources: dict[str, list[str]], trace_id: str) -> list[Event]:
    """Merge events from many sources into one chronological timeline.

    `sources` maps a source name (service/file) to its list of log lines.
    Events without a parseable timestamp are sorted last, preserving input order.
    """
    all_events: list[Event] = []
    for source, lines in sources.items():
        all_events.extend(extract_events(lines, trace_id, source))

    # Sort by timestamp; Nones go last. Use an index for a stable tiebreak.
    def key(item):
        idx, ev = item
        if ev.timestamp is None:
            return (1, idx)
        # offset-naive vs aware can't be compared; bucket naive as a 0-epoch shift
        ts = ev.timestamp
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return (0, ts.timestamp())

    indexed = list(enumerate(all_events))
    indexed.sort(key=key)
    return [ev for _, ev in indexed]


def timeline_span_seconds(events: list[Event]) -> float | None:
    """Wall-clock seconds between the first and last timestamped events."""
    stamped = [e.timestamp for e in events if e.timestamp is not None]
    if len(stamped) < 2:
        return None
    norm = [t.replace(tzinfo=timezone.utc) if t.tzinfo is None else t for t in stamped]
    return (max(norm) - min(norm)).total_seconds()
