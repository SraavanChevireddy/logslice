# logslice

> Follow one request across all your services. Point `logslice` at a pile of microservice log files and a trace id, and it reconstructs the full, chronologically-ordered journey — distributed tracing without a $$$ observability stack.

[![CI](https://github.com/SraavanChevireddy/logslice/actions/workflows/ci.yml/badge.svg)](https://github.com/SraavanChevireddy/logslice/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)

When a request fails somewhere across five services, you end up `grep`-ing the same trace id in five terminals and mentally interleaving timestamps. **logslice** does that for you: it scans every log file, pulls the lines for your trace id, parses each timestamp (across different log formats), and merges them into one timeline you can actually read.

No agents, no collector, no vendor. Just your existing log files.

## Features

- **Cross-format timestamp parsing** — ISO-8601 with `Z` or offsets, space-separated, comma millis. Mixed timezones are normalized to UTC so ordering is correct.
- **Plain-text *and* JSON logs** — finds the trace id as a substring or in fields like `trace_id`, `traceId`, `correlation_id`.
- **One unified timeline** with the source service on every line, plus total wall-clock span.
- **Pipe-friendly** — `--json` output for further processing.
- **Zero dependencies** — pure standard library.

## Install

```bash
pip install logslice          # from PyPI (once published)
# or from source:
git clone https://github.com/SraavanChevireddy/logslice.git
cd logslice && pip install -e .
```

## Usage

```bash
logslice <trace_id> <log files...>

# Follow a request across three services
logslice req-7f3a examples/*.log

# Machine-readable output
logslice req-7f3a logs/*.log --json
```

### Example

```bash
$ logslice req-7f3a examples/*.log

Timeline for trace 'req-7f3a'  (8 events across 3 sources, span 0.512s)

  2024-01-01T12:00:00+00:00         gateway.log          GET /checkout received from 10.0.0.5
  2024-01-01T12:00:00.050000+00:00  order-service.log    creating order
  2024-01-01T12:00:00.060000+00:00  order-service.log    calling payment-service
  2024-01-01T12:00:00.070000        payment-service.log  charging card
  2024-01-01T12:00:00.380000        payment-service.log  gateway slow, retried once
  2024-01-01T12:00:00.390000        payment-service.log  charge approved
  2024-01-01T12:00:00.400000+00:00  order-service.log    order persisted id=8821
  2024-01-01T12:00:00.512000+00:00  gateway.log          responded 200 in 512ms
```

In one glance: the request spent ~330ms inside the payment service, and that retry on the slow gateway explains the latency. Three different log formats, one coherent story.

## How it works

1. Read each file and split into lines.
2. Keep only lines that reference the trace id (substring or JSON field).
3. Extract a timestamp from each line with a tolerant regex.
4. Normalize timezones to UTC and stable-sort. Lines with no timestamp sort last, keeping their original order.

It's all pure functions in [`logslice/core.py`](logslice/core.py) — easy to read, test, and extend.

## Roadmap / contributing

Ideas worth a PR: gap detection (highlight the biggest time jump), latency-per-service summary, gzipped log support, reading from stdin. Keep the core dependency-free.

## License

[MIT](LICENSE) © Sraavan Chevireddy
