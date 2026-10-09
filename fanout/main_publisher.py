"""Stage 1 of fan-out: aggregated topic -> fan-out topic.

A single consumer group reads every aggregated window and republishes it to
the fan-out topic that cluster publishers subscribe to. Flushing is batched
on a timer (not per message) so throughput doesn't collapse.

Run:
    python -m fanout.main_publisher [--input-topic X --output-topic Y]
"""

from __future__ import annotations

import argparse
import json
import logging
import signal
import time

import config

log = logging.getLogger("livepulse.main_publisher")


def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="LivePulse main publisher")
    p.add_argument("--bootstrap-servers", default=config.KAFKA_BOOTSTRAP_SERVERS)
    p.add_argument("--input-topic", default=config.AGG_EVENTS_TOPIC)
    p.add_argument("--output-topic", default=config.FANOUT_TOPIC)
    p.add_argument("--flush-sec", type=float, default=config.MAIN_PUBLISHER_FLUSH_SEC)
    return p.parse_args(argv)


def run() -> None:
    args = parse_args()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    from kafka import KafkaConsumer, KafkaProducer

    stop = False

    def _handle(_signum, _frame):
        nonlocal stop
        stop = True

    signal.signal(signal.SIGINT, _handle)
    signal.signal(signal.SIGTERM, _handle)

    consumer = KafkaConsumer(
        args.input_topic,
        bootstrap_servers=args.bootstrap_servers,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset="latest",
        enable_auto_commit=True,
        group_id="livepulse-main-publisher",
    )
    producer = KafkaProducer(
        bootstrap_servers=args.bootstrap_servers,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        linger_ms=int(args.flush_sec * 1000),
        retries=3,
    )
    log.info(
        "forwarding %s -> %s (flush every %.2fs)",
        args.input_topic, args.output_topic, args.flush_sec,
    )

    last_flush = time.time()
    try:
        for message in consumer:
            if stop:
                break
            producer.send(args.output_topic, message.value)
            if time.time() - last_flush >= args.flush_sec:
                producer.flush()
                last_flush = time.time()
    finally:
        producer.flush()
        consumer.close()
        log.info("main publisher stopped")


if __name__ == "__main__":
    run()
