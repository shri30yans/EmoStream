"""HTTP ingest API: receives reaction events, buffers them, forwards to Kafka.

Design notes (what changed vs the prototype):
- Request path never blocks on Kafka. Events go into a bounded in-memory
  queue; a single background thread flushes every
  PRODUCER_FLUSH_INTERVAL_SEC. The old code spawned one thread per request
  and called producer.flush() inline, which collapses under load.
- All payloads are validated (see app/schemas.py). Invalid bodies get 400,
  missing/failed broker gets 503 -- never a fake 200.
- Canonical endpoint is POST /v1/reactions. POST /send_emoji is kept as a
  deprecated alias so old clients keep working.
- GET /healthz for orchestrators, GET /v1/stats for demos/debugging.
"""

from __future__ import annotations

import json
import logging
import queue
import threading
import time
from typing import Any, Optional

from flask import Flask, jsonify, request

import config
from app.schemas import validate_reaction

log = logging.getLogger("livepulse.ingest")


class BufferedProducer:
    """Thread-safe bounded buffer in front of a kafka KafkaProducer.

    The producer dependency is injected so unit tests can pass a fake.
    """

    def __init__(
        self,
        producer: Any,
        topic: str,
        flush_interval_sec: float = 0.5,
        maxsize: int = 50_000,
    ) -> None:
        self._producer = producer
        self._topic = topic
        self._flush_interval = flush_interval_sec
        self._queue: queue.Queue = queue.Queue(maxsize=maxsize)
        self._dropped = 0
        self._accepted = 0
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._thread = threading.Thread(
            target=self._flush_loop, name="kafka-flush", daemon=True
        )
        self._thread.start()

    def submit(self, event: dict) -> bool:
        try:
            self._queue.put_nowait(event)
        except queue.Full:
            with self._lock:
                self._dropped += 1
            return False
        with self._lock:
            self._accepted += 1
        return True

    def _flush_loop(self) -> None:
        while not self._stop.is_set():
            time.sleep(self._flush_interval)
            self.flush()

    def flush(self) -> None:
        batch = []
        while True:
            try:
                batch.append(self._queue.get_nowait())
            except queue.Empty:
                break
        for event in batch:
            try:
                self._producer.send(self._topic, event)
            except Exception:  # noqa: BLE001 -- must not kill flush thread
                log.exception("kafka send failed; event dropped")
        if batch:
            try:
                self._producer.flush()
            except Exception:  # noqa: BLE001
                log.exception("kafka flush failed")

    def stats(self) -> dict:
        with self._lock:
            return {
                "accepted": self._accepted,
                "dropped": self._dropped,
                "queued": self._queue.qsize(),
            }

    def close(self) -> None:
        self._stop.set()
        self.flush()


def _build_real_producer() -> Any:
    from kafka import KafkaProducer

    return KafkaProducer(
        bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        linger_ms=int(config.PRODUCER_FLUSH_INTERVAL_SEC * 1000),
        retries=3,
    )


def create_app(producer: Any = None, topic: Optional[str] = None) -> Flask:
    app = Flask(__name__)
    app.config["BUFFERED_PRODUCER"] = None

    lazy_topic = topic or config.RAW_EVENTS_TOPIC
    lazy_producer_holder: dict = {"producer": producer}

    def get_buffered() -> Optional[BufferedProducer]:
        if app.config["BUFFERED_PRODUCER"] is not None:
            return app.config["BUFFERED_PRODUCER"]
        if lazy_producer_holder["producer"] is None:
            try:
                lazy_producer_holder["producer"] = _build_real_producer()
            except Exception:  # noqa: BLE001 -- broker down at import time
                log.exception("could not connect to kafka at startup")
                return None
        app.config["BUFFERED_PRODUCER"] = BufferedProducer(
            lazy_producer_holder["producer"],
            lazy_topic,
            flush_interval_sec=config.PRODUCER_FLUSH_INTERVAL_SEC,
            maxsize=config.PRODUCER_QUEUE_MAX,
        )
        return app.config["BUFFERED_PRODUCER"]

    # Eagerly build when a producer (real or fake) was injected, so tests
    # exercise the real path. Otherwise lazy-connect on first request.
    if producer is not None:
        app.config["BUFFERED_PRODUCER"] = BufferedProducer(
            producer,
            lazy_topic,
            flush_interval_sec=config.PRODUCER_FLUSH_INTERVAL_SEC,
            maxsize=config.PRODUCER_QUEUE_MAX,
        )

    @app.get("/healthz")
    def healthz():
        buffered = get_buffered()
        kafka_ok = buffered is not None
        status = 200 if kafka_ok else 503
        return jsonify({"status": "ok" if kafka_ok else "degraded",
                        "kafka": "up" if kafka_ok else "down"}), status

    @app.get("/v1/stats")
    def stats():
        buffered = get_buffered()
        return jsonify((buffered.stats() if buffered else {"accepted": 0,
                        "dropped": 0, "queued": 0})), 200

    def _ingest():
        payload = request.get_json(silent=True)
        event, error = validate_reaction(payload)
        if error is not None:
            return jsonify({"status": "error", "error": error}), 400
        buffered = get_buffered()
        if buffered is None:
            return jsonify({"status": "error",
                            "error": "event broker unavailable"}), 503
        assert event is not None
        if not buffered.submit(event.to_kafka_dict()):
            return jsonify({"status": "error",
                            "error": "ingest buffer full, retry later"}), 503
        return jsonify({"status": "accepted"}), 202

    @app.post("/v1/reactions")
    def ingest():
        return _ingest()

    # Deprecated alias from the original prototype.
    @app.post("/send_emoji")
    def ingest_legacy():
        return _ingest()

    return app


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    app = create_app()
    log.info(
        "ingest listening on %s:%d -> kafka %s topic %s",
        config.API_HOST, config.API_PORT,
        config.KAFKA_BOOTSTRAP_SERVERS, config.RAW_EVENTS_TOPIC,
    )
    app.run(host=config.API_HOST, port=config.API_PORT, debug=False)


if __name__ == "__main__":
    main()
