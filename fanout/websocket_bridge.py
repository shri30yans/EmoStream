"""Stage 3 of fan-out: Kafka cluster topic -> WebSocket browsers/devices.

This is the single canonical bridge (it replaces three divergent prototype
scripts that disagreed on topic names and had broken asyncio usage).
One bridge serves one cluster topic on one WS port; run one per shard.

Fixes vs the prototype:
- Defines the missing connection handler (the old subscriber referenced an
  undefined ``websocket_handler`` and crashed on start).
- Never calls asyncio.run() inside the consumer loop; a background thread
  feeds an asyncio.Queue instead.
- Tracks connected sockets in a set guarded by the event loop, removes dead
  sockets on send failure instead of leaking them.

Run:
    python -m fanout.websocket_bridge [--topic streamagg.fanout.v1 --port 8765]
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import threading

import config

log = logging.getLogger("streamagg.ws_bridge")


def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="StreamAgg Kafka->WebSocket bridge")
    p.add_argument("--bootstrap-servers", default=config.KAFKA_BOOTSTRAP_SERVERS)
    p.add_argument("--topic", default=config.FANOUT_TOPIC)
    p.add_argument("--host", default=config.WS_HOST)
    p.add_argument("--port", type=int, default=config.WS_PORT)
    return p.parse_args(argv)


async def _serve(args: argparse.Namespace) -> None:
    import websockets

    connected: set = set()
    bus: asyncio.Queue = asyncio.Queue(maxsize=1000)

    async def handle(ws) -> None:
        connected.add(ws)
        try:
            await ws.wait_closed()
        finally:
            connected.discard(ws)

    async def broadcaster() -> None:
        while True:
            message = await bus.get()
            dead = []
            for ws in list(connected):
                try:
                    await ws.send(message)
                except Exception:  # noqa: BLE001 -- drop dead sockets
                    dead.append(ws)
            for ws in dead:
                connected.discard(ws)

    def kafka_loop(loop: asyncio.AbstractEventLoop) -> None:
        from kafka import KafkaConsumer

        consumer = KafkaConsumer(
            args.topic,
            bootstrap_servers=args.bootstrap_servers,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            auto_offset_reset="latest",
            enable_auto_commit=True,
            group_id=f"streamagg-ws-{args.port}",
        )
        for message in consumer:
            payload = json.dumps(message.value)
            try:
                asyncio.run_coroutine_threadsafe(bus.put(payload), loop)
            except Exception:  # noqa: BLE001
                log.exception("dropping message: bridge queue full")

    async with websockets.serve(handle, args.host, args.port):
        log.info("bridge %s -> ws://%s:%d", args.topic, args.host, args.port)
        loop = asyncio.get_running_loop()
        worker = threading.Thread(target=kafka_loop, args=(loop,), daemon=True)
        worker.start()
        await broadcaster()


def run() -> None:
    args = parse_args()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    asyncio.run(_serve(args))


if __name__ == "__main__":
    run()
