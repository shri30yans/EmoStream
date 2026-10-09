"""Pure-Python aggregation helpers shared by Spark and tests.

Extracting this from the Spark job matters: the downsampling rule can be
unit-tested in milliseconds without a Spark cluster.
"""

from __future__ import annotations

from collections import Counter


def downsample_count(raw_count: int, per_unit: int = 1000) -> int:
    """Condense a raw reaction count into fan-out units.

    - 0 reactions -> 0
    - 1..per_unit -> 1 (every reaction type seen in a window is reported)
    - above that, integer-divide so payloads stay small during viral spikes.

    >>> downsample_count(0), downsample_count(5), downsample_count(2500)
    (0, 1, 2)
    """
    if raw_count <= 0:
        return 0
    if raw_count <= per_unit:
        return 1
    return raw_count // per_unit


def aggregate_window(counts: dict[str, int], per_unit: int = 1000) -> list[dict]:
    """Turn {reaction: raw_count} for one window into a sorted payload list."""
    counter = Counter(counts)
    payload = [
        {"reaction": reaction, "count": downsample_count(n, per_unit),
         "raw_count": n}
        for reaction, n in counter.items()
    ]
    payload.sort(key=lambda row: row["raw_count"], reverse=True)
    return payload
