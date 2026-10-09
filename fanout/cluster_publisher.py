"""Stage 2 of fan-out: fan-out topic -> per-cluster topic.

Deploy one cluster publisher per audience shard (region, venue section,
stream edge). Each publisher filters or passes through aggregated windows
onto its own topic so subscribers only read their shard's traffic.

Run:
    python -m fanout.cluster_publisher --cluster-id eu-west
"""

from __future__ import annotations

import argparse
import json
import logging
import signal

import config

log = logging.getLogger("livepulse.cluster_publisher")


def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="LivePulse cluster publisher")
    p.add_argument("--bootstrap-servers", default=config.KAFKA_BOOTSTRAP_SERVERS)
    p.add_argument("--input-topic", default=config.FANOUT_TOPIC)
    p.add_argument("--cluster-id", default="default")
    p.add_argument(
        "--output-topic",
        default=None,
        help="Defaults to {fanout}.{cluster-id} when omitted.",
    )
    return p.parse_args(argv)


def run() -> None:
    args = parse_args()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    output_topic = args.output_topic or f"{config.FANOUT_TOPIC}.{args.cluster_id}"

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
        group_id=f"livepulse-cluster-{args.cluster_id}",
    )
    producer = KafkaProducer(
        bootstrap_servers=args.bootstrap_servers,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        retries=3,
    )
    log.info(
        "cluster %s: forwarding %s -> %s",
        args.cluster_id, args.input_topic, output_topic,
    )
    try:
        for message in consumer:
            if stop:
                break
            payload = message.value
            # Attach routing metadata once; downstream clients can ignore it.
            if isinstance(payload, dict):
                payload = {**payload, "cluster_id": args.cluster_id}
            producer.send(output_topic, payload)
            producer.flush()
    finally:
        producer.flush()
        consumer.close()
        log.info("cluster publisher %s stopped", args.cluster_id)


if __name__ == "__main__":
    run()
