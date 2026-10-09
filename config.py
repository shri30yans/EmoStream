"""Single source of truth for LivePulse-Kafka-Spark configuration.

Every topic name, port, interval, and threshold is driven by environment
variables with sane local defaults so the whole pipeline can be re-pointed
without editing code.
"""

from __future__ import annotations

import os


def _get(name: str, default: str) -> str:
    value = os.getenv(name, default)
    return value if value != "" else default


def _get_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def _get_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default


KAFKA_BOOTSTRAP_SERVERS: str = _get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

# Topic names. Versioned (v1) so future schema changes don't collide.
RAW_EVENTS_TOPIC: str = _get("RAW_EVENTS_TOPIC", "livepulse.raw.v1")
AGG_EVENTS_TOPIC: str = _get("AGG_EVENTS_TOPIC", "livepulse.agg.v1")
FANOUT_TOPIC: str = _get("FANOUT_TOPIC", "livepulse.fanout.v1")

# Ingest API
API_HOST: str = _get("API_HOST", "0.0.0.0")
API_PORT: int = _get_int("API_PORT", 5000)
PRODUCER_FLUSH_INTERVAL_SEC: float = _get_float("PRODUCER_FLUSH_INTERVAL_SEC", 0.5)
PRODUCER_QUEUE_MAX: int = _get_int("PRODUCER_QUEUE_MAX", 50_000)

# Stream processing (Spark micro-batch)
WINDOW_SECONDS: int = _get_int("WINDOW_SECONDS", 2)
# Downsampling: how many raw reactions one emitted unit represents.
# e.g. 1000 raw "fire" reactions in a window -> count 1 unit of "fire"
# (x1000). Keeps fan-out payloads small during viral moments.
DOWNSAMPLE_PER_UNIT: int = _get_int("DOWNSAMPLE_PER_UNIT", 1000)
SPARK_CHECKPOINT_DIR: str = _get("SPARK_CHECKPOINT_DIR", "/tmp/livepulse-checkpoint")
SPARK_APP_NAME: str = _get("SPARK_APP_NAME", "LivePulseKafkaSparkAggregator")

# Fan-out
MAIN_PUBLISHER_FLUSH_SEC: float = _get_float("MAIN_PUBLISHER_FLUSH_SEC", 0.5)
WS_HOST: str = _get("WS_HOST", "localhost")
WS_PORT: int = _get_int("WS_PORT", 8765)

# Demo / load tool defaults
API_BASE_URL: str = _get("API_BASE_URL", f"http://localhost:{API_PORT}")
