from datetime import timezone

from logslice.core import (
    build_timeline,
    extract_events,
    line_matches,
    parse_timestamp,
    timeline_span_seconds,
)


def test_parse_iso_z():
    dt = parse_timestamp("2024-01-01T12:00:00.500Z hello")
    assert dt is not None
    assert dt.tzinfo == timezone.utc
    assert dt.year == 2024 and dt.second == 0


def test_parse_space_separated():
    dt = parse_timestamp("2024-01-01 12:00:00 INFO started")
    assert dt is not None and dt.hour == 12


def test_parse_no_timestamp():
    assert parse_timestamp("just a message") is None


def test_line_matches_substring():
    assert line_matches("req trace=abc123 done", "abc123")
    assert not line_matches("req trace=xyz done", "abc123")


def test_line_matches_json_field():
    assert line_matches('{"trace_id": "abc123", "msg": "ok"}', "abc123")
    assert line_matches('{"traceId": "abc123"}', "abc123")
    assert not line_matches('{"trace_id": "other"}', "abc123")


def test_extract_events_filters_by_trace():
    lines = [
        "2024-01-01T12:00:00Z trace=abc123 start",
        "2024-01-01T12:00:01Z trace=zzz other",
        "2024-01-01T12:00:02Z trace=abc123 end",
    ]
    events = extract_events(lines, "abc123", "svc")
    assert len(events) == 2
    assert all(e.source == "svc" for e in events)


def test_build_timeline_orders_across_sources():
    gateway = ["2024-01-01T12:00:00Z trace=abc123 gateway received"]
    service = [
        "2024-01-01T12:00:02Z trace=abc123 service done",
        "2024-01-01T12:00:01Z trace=abc123 service start",
    ]
    timeline = build_timeline({"gateway": gateway, "service": service}, "abc123")
    msgs = [e.raw.split("trace=abc123 ")[1] for e in timeline]
    assert msgs == ["gateway received", "service start", "service done"]


def test_timeline_handles_mixed_timezones():
    # 12:00:00Z == 13:00:00+01:00, so the +01:00 line should sort first by 1s.
    a = ["2024-01-01T12:00:05Z trace=abc123 utc line"]
    b = ["2024-01-01T13:00:00+01:00 trace=abc123 offset line"]  # == 12:00:00Z
    timeline = build_timeline({"a": a, "b": b}, "abc123")
    assert "offset line" in timeline[0].raw


def test_span_seconds():
    lines = [
        "2024-01-01T12:00:00Z trace=abc123 start",
        "2024-01-01T12:00:03Z trace=abc123 end",
    ]
    timeline = build_timeline({"s": lines}, "abc123")
    assert timeline_span_seconds(timeline) == 3.0


def test_lines_without_timestamp_sort_last():
    lines = [
        "trace=abc123 no timestamp here",
        "2024-01-01T12:00:00Z trace=abc123 stamped",
    ]
    timeline = build_timeline({"s": lines}, "abc123")
    assert timeline[-1].timestamp is None
